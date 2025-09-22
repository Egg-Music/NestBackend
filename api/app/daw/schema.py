execute_actions_tool = {
  "name": "execute_actions",
  "description": "Validate and execute a short plan of DAW actions. Prefer minimal, reversible plans. The names of actions must match the allowed types exactly.",
  "parameters": {
    "type": "object",
    "properties": {
      "mode": {
        "type": "string",
        "enum": ["dryRun", "apply"],
        "description": "Use dryRun to preview diffs before apply."
      },
      "plan": {
        "type": "array",
        "minItems": 1,
        "maxItems": 32,
        "items": {
          "anyOf": [
            { "type":"object", "properties": { "type":{"type":"string","enum":["project.setTitle"]}, "title":{"type":"string"} }, "required":["type","title"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["transport.play"]} }, "required":["type"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["transport.stop"]} }, "required":["type"], "additionalProperties": False },
            { "type":"object", "properties": {
                "type":{"type":"string","enum":["loop.set"]},
                "startBeat":{"type":"number","minimum":0},
                "lengthBeats":{"type":"number","exclusiveMinimum":0}
              }, "required":["type","startBeat","lengthBeats"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["track.add"]}, "name":{"type":"string"}, "color":{"type":"string"} }, "required":["type","name"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["track.rename"]}, "trackId":{"type":"string"}, "name":{"type":"string"} }, "required":["type","trackId","name"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["track.setGain"]}, "trackId":{"type":"string"}, "gain":{"type":"number"} }, "required":["type","trackId","gain"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["track.toggleMute"]}, "trackId":{"type":"string"} }, "required":["type","trackId"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["track.setColor"]}, "trackId":{"type":"string"}, "color":{"type":"string"} }, "required":["type","trackId","color"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["clip.addAudio"]}, "trackId":{"type":"string"}, "startBeat":{"type":"number","minimum":0}, "path":{"type":"string"} }, "required":["type","trackId","startBeat","path"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["clip.move"]}, "clipId":{"type":"string"}, "startBeat":{"type":"number","minimum":0} }, "required":["type","clipId","startBeat"], "additionalProperties": False },
            { "type":"object", "properties": { 
                "type":{"type":"string","enum":["fx.setParam"]},
                "target": {"type":"object", "properties": {
                    "trackId": {"type":"string"},
                    "unit": {"type":"string", "enum":["reverb","comp","eq"]},
                    "path": {"type":"string"}
                }, "required":["trackId","unit","path"], "additionalProperties": False},
                "value": {"type":["number","boolean","string"]}
              }, "required":["type","target","value"], "additionalProperties": False },
            { "type":"object", "properties": { 
                "type":{"type":"string","enum":["fx.addUnit"]}, 
                "trackId":{"type":"string"}, 
                "unit":{"type":"string","enum":["reverb","comp","eq"]}, 
                "slot":{"type":"integer","minimum":0},
                "bypass":{"type":"boolean"},
                "params":{"type":"object","additionalProperties": {"type":["number","boolean","string"]}}
              }, "required":["type","trackId","unit"], "additionalProperties": False },
            { "type":"object", "properties": { 
                "type":{"type":"string","enum":["fx.setParams"]},
                "target": {"type":"object", "properties": {
                    "trackId": {"type":"string"},
                    "unit": {"type":"string", "enum":["reverb","comp","eq"]},
                    "fxId": {"type":"string"}
                }, "required":["trackId","unit"], "additionalProperties": False},
                "params":{"type":"object","additionalProperties": {"type":["number","boolean","string"]}}
              }, "required":["type","target","params"], "additionalProperties": False },
            { "type":"object", "properties": { 
                "type":{"type":"string","enum":["fx.setBypass"]},
                "target": {"type":"object", "properties": {
                    "trackId": {"type":"string"},
                    "unit": {"type":"string", "enum":["reverb","comp","eq"]},
                    "fxId": {"type":"string"}
                }, "required":["trackId","unit"], "additionalProperties": False},
                "bypass":{"type":"boolean"}
              }, "required":["type","target","bypass"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["fx.removeUnit"]}, "trackId":{"type":"string"}, "fxId":{"type":"string"}, "unit":{"type":"string","enum":["reverb","comp","eq"]} }, "required":["type","trackId"], "additionalProperties": False },
            { "type":"object", "properties": { 
                "type":{"type":"string","enum":["eq.batchSet"]},
                "trackId":{"type":"string"},
                "changes": {"type":"array","items": {"type":"object","properties": {"path":{"type":"string"}, "value":{"type":["number","boolean","string"]}}, "required":["path","value"], "additionalProperties": False}, "minItems": 1}
              }, "required":["type","trackId","changes"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["eq.addUnit"]}, "trackId":{"type":"string"}, "slot":{"type":"integer","minimum":0} }, "required":["type","trackId"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["eq.setParam"]}, "trackId":{"type":"string"}, "path":{"type":"string"}, "value": {"type":["number","boolean","string"]} }, "required":["type","trackId","path","value"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["transport.set"]}, "beat":{"type":"number","minimum":0} }, "required":["type","beat"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["project.setMeta"]}, "title":{"type":"string"}, "tempo":{"type":"number","exclusiveMinimum":0} }, "required":["type"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["project.save"]}, "path":{"type":"string"} }, "required":["type"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["project.open"]}, "path":{"type":"string"} }, "required":["type","path"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["track.delete"]}, "trackId":{"type":"string"} }, "required":["type","trackId"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["tracks.setActive"]}, "ids":{"type":"array","items":{"type":"string"}, "minItems":1} }, "required":["type","ids"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["clip.delete"]}, "clipId":{"type":"string"} }, "required":["type","clipId"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["clips.deleteMany"]}, "ids":{"type":"array","items":{"type":"string"}, "minItems":1} }, "required":["type","ids"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["clip.duplicate"]}, "clipId":{"type":"string"} }, "required":["type","clipId"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["clip.splitAtBeat"]}, "clipId":{"type":"string"}, "beat":{"type":"number","minimum":0} }, "required":["type","clipId","beat"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["clip.rename"]}, "clipId":{"type":"string"}, "name":{"type":"string"} }, "required":["type","clipId","name"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["clip.setLayer"]}, "clipId":{"type":"string"}, "layer":{"type":"number"} }, "required":["type","clipId","layer"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["clip.setBounds"]}, "clipId":{"type":"string"}, "startBeat":{"type":"number"}, "lengthBeats":{"type":"number"}, "fileOffsetSeconds":{"type":"number"} }, "required":["type","clipId"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["clip.setGainPan"]}, "clipId":{"type":"string"}, "gain":{"type":"number"}, "pan01":{"type":"number"} }, "required":["type","clipId"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["xf.createOverlap"]}, "aId":{"type":"string"}, "bId":{"type":"string"}, "trackId":{"type":"string"} }, "required":["type","aId","bId"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["xf.update"]}, "id":{"type":"string"}, "startBeats":{"type":"number"}, "lengthBeats":{"type":"number"}, "curve":{"type":"string","enum":["equal","linear"]} }, "required":["type","id"], "additionalProperties": False },
            { "type":"object", "properties": { "type":{"type":"string","enum":["xf.remove"]}, "id":{"type":"string"} }, "required":["type","id"], "additionalProperties": False }
          ]
        }
      }
    },
    "required": ["plan"],
    "additionalProperties": False
  }
}

# Removed separate FX tools to keep single-tool contract (execute_actions only)