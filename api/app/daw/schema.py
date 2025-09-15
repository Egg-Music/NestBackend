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
                    "unit": {"type":"string", "enum":["eq","comp","verb"]},
                    "path": {"type":"string"}
                }, "required":["trackId","unit","path"], "additionalProperties": False},
                "value": {"type":"number"}
              }, "required":["type","target","value"], "additionalProperties": False }
          ]
        }
      }
    },
    "required": ["plan"],
    "additionalProperties": False
  }
}