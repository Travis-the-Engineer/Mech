"""Example bot: walk to the zone, grab a weapon, shoot the nearest mech, draw what it's thinking."""
import math
import mechfight as mf


class Bot:
    name = "example-py"

    def __init__(self, hello: mf.Hello):
        self.reach = hello["config"]["loot"]["pickup_radius"]
        self.last_hp = None
    def act(self, obs: mf.Observation) -> mf.Action:
        me = obs["self"]
        x, y, z = me["pos"]
        goal = obs["zone"]["next_center"]
        hp = me["hp"]
        took_damage = self.last_hp is not None and hp < self.last_hp
        self.last_hp = hp
        act: mf.Action = {"tick": obs["tick"]}
        if obs["offer"]:
            act["pick"] = 0
        pickups = sorted(
            obs["pickups"],
            key=lambda p: math.dist(p["pos"][:2], (x, y)),
        )
        near = [p for p in pickups if math.dist(p["pos"][:2], (x, y)) < self.reach]
        if near:
            act["take"] = near[0]["id"]

        move_target = pickups[0]["pos"] if (pickups and me["in_zone"]) else goal
        enemies = sorted((m for m in obs["mechs"] if m["kind"] == "mech"), key=lambda m: math.dist(m["pos"], me["pos"]))
        yaw = math.atan2(move_target[1] - y, move_target[0] - x)
        act.update(move=[math.cos(yaw), math.sin(yaw)], aim=[yaw, 0.0], boost=not me["in_zone"])
        act.update(move=[math.cos(yaw), math.sin(yaw)], aim=[yaw, 0.0], boost=not me["in_zone"])
        if enemies:
            t = enemies[0]["pos"]
            dist_to_enemy = math.dist(t[:2], (x, y))
            if took_damage or dist_to_enemy < self.reach * 4:
                aim = [math.atan2(t[1] - y, t[0] - x), math.atan2(t[2] - z - 2.5, dist_to_enemy)]
                act.update(aim=aim, fire=[True, True])
                mf.draw.line([x, y, z + 7], [t[0], t[1], t[2] + 4.5], "#ff5040")
        mf.draw.point([move_target[0], move_target[1], z], "#40c0ff", 6)
        mf.draw.label(f"hp {me['hp']:.0f} · {len(enemies)} in sight")
        return act


mf.run(Bot)
