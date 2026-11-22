import math
import mechfight as mf


class Bot:
    name = "crate-hunter-py"

    def __init__(self, hello: mf.Hello):
        self.reach = hello["config"]["loot"]["pickup_radius"]
        self.last_hp = None

    def act(self, obs: mf.Observation) -> mf.Action:
        me = obs["self"]
        x, y, z = me["pos"]
        hp = me["hp"]
        goal = obs["zone"]["next_center"]
        act: mf.Action = {"tick": obs["tick"]}

        took_damage = self.last_hp is not None and hp < self.last_hp
        self.last_hp = hp

        if obs["offer"]:
            act["pick"] = 0

        pickups = sorted(
            obs["pickups"],
            key=lambda p: math.dist(p["pos"][:2], (x, y)),
        )
        near = [
            p for p in pickups if math.dist(p["pos"][:2], (x, y)) < self.reach
        ]

        enemies = sorted(
            (m for m in obs["mechs"] if m["kind"] == "mech"),
            key=lambda m: math.dist(m["pos"], me["pos"]),
        )

        engaged_enemy = None
        if enemies:
            dist_to_enemy = math.dist(enemies[0]["pos"][:2], (x, y))
            if took_damage or dist_to_enemy < self.reach * 4:
                engaged_enemy = enemies[0]

        # Priority 1: Engage if threatened
        if engaged_enemy:
            t = engaged_enemy["pos"]
            ev = engaged_enemy["vel"]
            dist_to_enemy = math.dist(t[:2], (x, y))
            bullet_speed = 252.0
            travel_time = dist_to_enemy / bullet_speed
            predicted_x = t[0] + ev[0] * travel_time
            predicted_y = t[1] + ev[1] * travel_time
            aim = [
                math.atan2(predicted_y - y, predicted_x - x),
                math.atan2(t[2] - z - 2.5, dist_to_enemy),
            ]
            yaw = aim[0]
            act.update(
                move=[math.cos(yaw), math.sin(yaw)],
                aim=aim,
                fire=[True, True],
                boost=False,
            )
            mf.draw.line([x, y, z + 7], [t[0], t[1], t[2] + 4.5], "#ff5040")
            mf.draw.point([t[0], t[1], z], "#ff5040", 6)
            mf.draw.label(f"hp {hp:.0f} · ENGAGING")

        # Priority 2: Hide from known enemy
        elif enemies:
            enemy = enemies[0]
            yaw = math.atan2(y - enemy["pos"][1], x - enemy["pos"][0])
            act.update(
                move=[math.cos(yaw), math.sin(yaw)],
                aim=[yaw, 0.0],
                boost=not me["in_zone"],
            )
            mf.draw.point([x, y, z], "#40c0ff", 6)
            mf.draw.label(f"hp {hp:.0f} · HIDING")

        # Priority 3: Pick up within reach
        elif near:
            act["take"] = near[0]["id"]
            target = near[0]["pos"]
            yaw = math.atan2(target[1] - y, target[0] - x)
            act.update(
                move=[math.cos(yaw), math.sin(yaw)],
                aim=[yaw, 0.0],
                boost=not me["in_zone"],
            )
            mf.draw.point([target[0], target[1], z], "#40c0ff", 6)
            mf.draw.label(f"hp {hp:.0f} · LOOTING")

        # Priority 4: Go to nearest loot
        elif pickups and me["in_zone"]:
            target = pickups[0]["pos"]
            yaw = math.atan2(target[1] - y, target[0] - x)
            act.update(
                move=[math.cos(yaw), math.sin(yaw)],
                aim=[yaw, 0.0],
                boost=not me["in_zone"],
            )
            mf.draw.point([target[0], target[1], z], "#40c0ff", 6)
            mf.draw.label(f"hp {hp:.0f} · GOING TO LOOT")

        # Fallback: Go to zone center
        else:
            yaw = math.atan2(goal[1] - y, goal[0] - x)
            act.update(
                move=[math.cos(yaw), math.sin(yaw)],
                aim=[yaw, 0.0],
                boost=not me["in_zone"],
            )
            mf.draw.point([goal[0], goal[1], z], "#40c0ff", 6)
            mf.draw.label(f"hp {hp:.0f} · ZONE")

        return act
