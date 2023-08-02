import csv
import itertools
import json
import operator
import re

with open("ally-turf.csv") as f:
    voters = list(csv.DictReader(f))


def make_door_key(v):
    return (v["housenumber"], v["streetname"], v["streettype"], v["streetquad"])


voter_fields = "statevoterid activeinactive firstname middlename lastname city cellphone landlinephone gender race birthdate regdate".split()


def groupby(xs, k):
    return itertools.groupby(sorted(xs, key=k), k)


data = {
    "turfs": [],
    "doors": [],
    "voters": [],
}


def add(x, obj):
    assert x in data
    assert isinstance(obj, dict)

    obj["_id"] = len(data[x])
    obj["notes"] = []
    obj["created_by"] = "system import"
    data[x].append(obj)

    return obj["_id"]


def numpart(x):
    return re.findall("^[0-9]+", x)[0]


def score_door(door_id, from_door_id):
    door = data["doors"][door_id]
    from_door = data["doors"][from_door_id]

    dist = ((float(door["lat"]) - float(from_door["lat"])) * 1000) ** 2 + (
        (float(door["lon"]) - float(from_door["lon"])) * 1000
    ) ** 2

    ad1 = int(numpart(door["address"]))
    ad2 = int(numpart(from_door["address"]))

    if door["address"].split()[1:] == from_door["address"].split()[1:]:
        dist -= 10
        if ad1 % 2 == ad2 % 2:
            dist -= 5

    return dist


def reorder_doors(turf):
    door_ids = turf["doors"]

    q = door_ids.copy()
    result_ids = [q.pop(0)]

    while q:
        cur = result_ids[-1]
        n = list(sorted(q, key=lambda k: score_door(k, cur)))[0]
        q.remove(n)
        result_ids.append(n)

    turf["doors"] = result_ids


for turf_desc, turf_voters in groupby(voters, operator.itemgetter("turfdesc")):
    turf = {
        "desc": turf_desc,
        "doors": [],
        "voters": [],
    }
    turf_id = add("turfs", turf)

    for door_key, door_voters in itertools.groupby(
        sorted(
            turf_voters,
            key=(
                lambda v: (
                    v["streetname"],
                    v["streettype"],
                    v["streetquad"],
                    int(numpart(v["housenumber"])),
                    v["housenumber"],
                )
            ),
        ),
        make_door_key,
    ):
        door = {
            "turf_id": turf_id,
            "address": " ".join([c for c in door_key if c]),
            "voters": [],
        }
        door_id = add("doors", door)

        turf["doors"].append(door_id)

        for voter in door_voters:
            door["lat"] = voter["geocodedlat"]
            door["lon"] = voter["geocodedlon"]

            voter = {k: voter[k] for k in voter_fields}
            voter_id = add("voters", voter)

            door["city"] = voter["city"]

            voter["door_id"] = door_id
            voter["turf_id"] = turf_id

            turf["voters"].append(voter_id)
            door["voters"].append(voter_id)

    reorder_doors(turf)

print(json.dumps(data))
