import csv
import itertools
import json
import operator
import re

with open("ally-turf.csv") as f:
    voters = list(csv.DictReader(f))


def make_door_key(v):
    return (v["housenumber"], v["streetname"], v["streettype"], v["streetquad"])


def reformat_phone(k):
    k = "".join([i for i in k if i.isnumeric()])
    return f"({k[:3]}) {k[3:6]}-{k[6:]}"


voter_fields = "statevoterid activeinactive firstname middlename lastname city cellphone landlinephone gender race birthdate regdate phonebankturf".split()


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
    routes = []

    door_ids = turf["doors"]
    for start_id in door_ids:
        q = door_ids.copy()

        result_ids = [start_id]
        q.remove(start_id)

        total_score = 0
        while q:
            cur = result_ids[-1]
            n = list(sorted(q, key=lambda k: score_door(k, cur)))[0]
            q.remove(n)
            result_ids.append(n)

            total_score += score_door(n, cur)

        routes.append((total_score, start_id, result_ids))

    routes.sort()
    turf["doors"] = routes[0][2]


all_turfs = {}


def get_turf_id(turf_desc):
    orig_turf_desc = turf_desc

    if turf_desc not in all_turfs:
        phone_key = ""

        if turf_desc.startswith("PHONEBANK: "):
            turf_desc = turf_desc[len("PHONEBANK: ") :]
            phone_key = "bestphone"

        elif turf_desc.startswith("TEXTBANK: "):
            turf_desc = turf_desc[len("TEXTBANK: ") :]

            # this is a bit goofy. by definition, bestphone is going to be mobile
            # EXCEPT if it's edited!! which we allow!!
            phone_key = "mobilephone"

        turf = {
            "desc": turf_desc,
            "phone_key": phone_key,
            "doors": [],
            "voters": [],
        }
        turf_id = add("turfs", turf)
        all_turfs[orig_turf_desc] = turf, turf_id

    return all_turfs[orig_turf_desc]


for turf_desc, turf_voters in groupby(voters, operator.itemgetter("turfdesc")):
    turf, turf_id = get_turf_id(turf_desc)

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

            if voter["phonebankturf"]:
                phonebank_turf, phonebank_turf_id = get_turf_id(voter["phonebankturf"])
                voter["phonebank_turf_id"] = phonebank_turf_id
                phonebank_turf["voters"].append(voter_id)

            voter["bestphone"] = None

            if voter["landlinephone"]:
                voter["bestphone"] = voter["landlinephone"]

            if voter["cellphone"]:
                voter["bestphone"] = voter["cellphone"]

            turf["voters"].append(voter_id)
            door["voters"].append(voter_id)

    reorder_doors(turf)


def reorder_voters(turf):
    phone_key = turf["phone_key"]
    voters = [data["voters"][i] for i in turf["voters"]]
    voters = [v for v in voters if phone_key in v and v[phone_key]]
    voters.sort(key=lambda v: reformat_phone(v[phone_key]))
    turf["voters"] = [v["_id"] for v in voters]


for turf in data["turfs"]:
    if not turf["phone_key"]:
        continue

    reorder_voters(turf)

print(json.dumps(data))
