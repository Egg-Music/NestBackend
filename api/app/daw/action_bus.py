from typing import Any, Dict, List, Literal, Tuple

Mode = Literal["dryRun", "apply"]
Diff = Dict[str, Any]  # {op, path, value}

def beats_to_seconds(beat: float, bpm: float, beat_unit: int = 4) -> float:
    return max(0.0, beat) * (60.0 / bpm) * (4.0 / beat_unit)

class ActionBus:
    def __init__(self, project_root: str = "", bpm: float = 120.0, beat_unit: int = 4):
        self.project_root = project_root
        self.bpm = bpm
        self.beat_unit = beat_unit

    def execute_plan(self, plan: List[Dict[str, Any]], mode: Mode = "apply") -> Tuple[List[Dict[str, Any]], List[Diff]]:
        results: List[Dict[str, Any]] = []
        diffs: List[Diff] = []
        # begin tx (call core.tx.begin if you have it)
        failed = False

        for a in plan:
            r, ds = self.dispatch(a, mode)
            results.append(r)
            if r.get("ok") and ds:
                diffs.extend(ds)
            if not r.get("ok"):
                failed = True
                break

        # commit/rollback here as needed
        return results, diffs

    def dispatch(self, action: Dict[str, Any], mode: Mode) -> Tuple[Dict[str, Any], List[Diff]]:
        t = action.get("type")
        if not t:
            return {"ok": False, "error": "missing type"}, []

        # NOTE: replace all branches below with real core calls
        if t == "project.setTitle":
            title = str(action["title"])
            if mode == "dryRun":
                return {"ok": True}, [{"op": "replace", "path": "/project/title", "value": title}]
            # core.project.setMeta(title=title)
            return {"ok": True}, [{"op": "replace", "path": "/project/title", "value": title}]

        if t == "transport.play":
            return {"ok": True}, [{"op": "replace", "path": "/transport/playing", "value": True}]

        if t == "transport.stop":
            return {"ok": True}, [{"op": "replace", "path": "/transport/playing", "value": False}]

        if t == "loop.set":
            sb = float(action["startBeat"]) ; lb = float(action["lengthBeats"])
            if lb <= 0: return {"ok": False, "error": "lengthBeats must be > 0"}, []
            return {"ok": True}, [
                {"op": "replace", "path": "/loop/startBeat", "value": sb},
                {"op": "replace", "path": "/loop/lengthBeats", "value": lb},
            ]

        if t == "track.add":
            name = str(action["name"])
            color = action.get("color")
            new_id = "t_" + name.lower().replace(" ", "_")
            track_value: Dict[str, Any] = {"id": new_id, "name": name}
            if color is not None:
                track_value["color"] = str(color)
            return {"ok": True, "meta": {"trackId": new_id}}, [
                {"op": "add", "path": "/tracks/-", "value": track_value}
            ]

        if t == "track.rename":
            return {"ok": True}, [{"op": "replace", "path": f"/tracks/{action['trackId']}/name", "value": str(action["name"])}]

        if t == "track.setGain":
            gain = float(action["gain"])  # API changed to `gain`
            return {"ok": True}, [{"op": "replace", "path": f"/tracks/{action['trackId']}/gain", "value": gain}]
        if t == "track.setColor":
            return {"ok": True}, [{"op": "replace", "path": f"/tracks/{action['trackId']}/color", "value": str(action["color"])}]

        if t == "fx.setParam":
            target = action["target"]
            track_id = str(target["trackId"]) ; unit = str(target["unit"]) ; path = str(target["path"]) 
            value_raw = action["value"]
            value: Any
            if isinstance(value_raw, (int, float)):
                value = float(value_raw)
            elif isinstance(value_raw, str):
                # allow string for enums like slope or type
                value = value_raw
            else:
                value = bool(value_raw)
            return {"ok": True}, [{"op": "replace", "path": f"/fx/{track_id}/{unit}/{path}", "value": value}]

        if t == "fx.setParams":
            target = action.get("target", {})
            track_id = str(target.get("trackId", action.get("trackId", "")))
            unit = str(target.get("unit", action.get("unit", "reverb")))
            params = action.get("params", {})
            diffs: List[Diff] = []
            for key, val in params.items():
                if isinstance(val, (int, float, bool, str)):
                    diffs.append({"op": "replace", "path": f"/fx/{track_id}/{unit}/{key}", "value": val})
            return {"ok": True}, diffs

        if t == "fx.addUnit":
            track_id = str(action.get("trackId") or action.get("track_id") or "")
            unit = str(action.get("unit", "reverb"))
            slot = action.get("slot")
            bypass = bool(action.get("bypass", False))
            params = action.get("params", {}) or {}
            fx_id = "fx_" + (track_id or "") + "_" + unit
            value: Dict[str, Any] = {"id": fx_id, "unit": unit, "bypass": bypass}
            diffs: List[Diff] = []
            # Add unit
            if slot is None:
                diffs.append({"op": "add", "path": f"/fx/{track_id}/units/-", "value": value})
            else:
                diffs.append({"op": "add", "path": f"/fx/{track_id}/units/{int(slot)}", "value": value})
            # Apply initial params
            for key, val in params.items():
                # EQ uses full paths like eq/bands/0/type
                if unit == "eq" and isinstance(key, str) and key.startswith("eq/"):
                    diffs.append({"op": "replace", "path": f"/fx/{track_id}/eq/{key[3:]}", "value": val})
                else:
                    diffs.append({"op": "replace", "path": f"/fx/{track_id}/{unit}/{key}", "value": val})
            return {"ok": True, "meta": {"fxId": fx_id}}, diffs

        if t == "fx.setBypass":
            track_id = str(action.get("trackId") or action.get("track_id") or "")
            fx_id = str(action.get("fxId") or action.get("fx_id") or "")
            bypass = bool(action.get("bypass", False))
            path = f"/fx/{track_id}/units/{fx_id}/bypass" if fx_id else f"/fx/{track_id}/reverb/bypass"
            return {"ok": True}, [{"op": "replace", "path": path, "value": bypass}]

        if t == "fx.removeUnit":
            track_id = str(action.get("trackId") or action.get("track_id") or "")
            fx_id = str(action.get("fxId") or action.get("fx_id") or "")
            if fx_id:
                return {"ok": True}, [{"op": "remove", "path": f"/fx/{track_id}/units/{fx_id}"}]
            # fallback: bypass default reverb
            return {"ok": True}, [{"op": "replace", "path": f"/fx/{track_id}/reverb/bypass", "value": True}]

        if t == "eq.batchSet":
            track_id = str(action.get("trackId") or action.get("track_id") or "")
            changes = action.get("changes", [])
            diffs: List[Diff] = []
            for ch in changes:
                p = ch.get("path"); v = ch.get("value")
                if not isinstance(p, str):
                    continue
                # If path already includes unit prefix, use as-is; otherwise prefix with unit
                full_path = p if p.startswith("/") else f"/fx/{track_id}/eq/{p}"
                diffs.append({"op": "replace", "path": full_path, "value": v})
            return {"ok": True}, diffs

        if t == "eq.addUnit":
            track_id = str(action.get("trackId") or action.get("track_id") or "")
            slot = action.get("slot")
            fx_id = "fx_" + (track_id or "") + "_eq"
            value: Dict[str, Any] = {"id": fx_id, "unit": "eq", "bypass": False}
            if slot is None:
                return {"ok": True, "meta": {"fxId": fx_id}}, [{"op": "add", "path": f"/fx/{track_id}/units/-", "value": value}]
            return {"ok": True, "meta": {"fxId": fx_id}}, [{"op": "add", "path": f"/fx/{track_id}/units/{int(slot)}", "value": value}]

        if t == "eq.setParam":
            track_id = str(action.get("trackId") or action.get("track_id") or "")
            path = str(action.get("path") or "")
            val = action.get("value")
            if not path:
                return {"ok": False, "error": "missing path"}, []
            full_path = path if path.startswith("/") else f"/fx/{track_id}/eq/{path}"
            return {"ok": True}, [{"op": "replace", "path": full_path, "value": val}]

        if t == "track.toggleMute":
            # In real code, read current mute from core; here we just flip to True as a placeholder
            return {"ok": True}, [{"op": "replace", "path": f"/tracks/{action['trackId']}/mute", "value": True}]

        if t == "clip.addAudio":
            # path checks omitted for brevity; do project-root enforcement in real code
            start_sec = beats_to_seconds(float(action["startBeat"]), self.bpm, self.beat_unit)
            # core.clip.add(trackId, startSeconds, path)
            clip_id = "c_" + str(abs(hash(action["path"])) % 10_000)
            return {"ok": True, "meta": {"clipId": clip_id}}, [
                {"op": "add", "path": "/clips/-", "value": {
                    "id": clip_id, "trackId": action["trackId"],
                    "startBeat": action["startBeat"], "path": action["path"]
                }}
            ]

        if t == "clip.move":
            return {"ok": True}, [{"op": "replace", "path": f"/clips/{action['clipId']}/startBeat", "value": float(action["startBeat"])}]

        return {"ok": False, "error": f"unsupported: {t}"}, []


