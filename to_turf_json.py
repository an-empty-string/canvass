import csv
import itertools
import json
import operator

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


for turf_desc, turf_voters in groupby(voters, operator.itemgetter("turfdesc")):
    turf = {
        "desc": turf_desc,
        "doors": [],
        "voters": [],
    }
    turf_id = add("turfs", turf)

    for door_key, door_voters in groupby(turf_voters, make_door_key):
        door = {
            "turf_id": turf_id,
            "address": " ".join([c for c in door_key if c]),
            "voters": [],
        }
        door_id = add("doors", door)

        turf["doors"].append(door_id)

        for voter in door_voters:
            voter = {k: voter[k] for k in voter_fields}
            voter_id = add("voters", voter)

            door["city"] = voter["city"]

            voter["door_id"] = door_id
            voter["turf_id"] = turf_id

            turf["voters"].append(voter_id)
            door["voters"].append(voter_id)

print(json.dumps(data))
