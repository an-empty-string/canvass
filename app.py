import datetime
import json
import os

from flask import Flask, g, redirect, render_template, request, url_for

app = Flask(__name__)

with open("database.json") as f:
    data = json.load(f)


def save_data():
    with open("database-new.json", "w") as f:
        json.dump(data, f)

    ts = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    os.rename("database.json", f"database-{ts}.json")
    os.rename("database-new.json", f"database.json")


@app.before_request
def before_request():
    g.canvasser = "tris emmy wilson"


@app.context_processor
def inject_data():
    return data


@app.context_processor
def inject_data_2():
    return {"is_dnc": is_dnc}


def is_dnc(v):
    for note in v["notes"]:
        if note["dnc"]:
            return True

    return False


@app.route("/turf/<int:id>/")
def show_turf(id):
    turf = data["turfs"][id]
    return render_template("turf.html", turf=turf)


@app.route("/door/<int:id>/")
def show_door(id):
    door = data["doors"][id]

    turf_doors = data["turfs"][door["turf_id"]]["doors"]
    idx = turf_doors.index(id)
    prev_door_id = next_door_id = None

    if idx > 0:
        prev_door_id = turf_doors[idx - 1]
    if idx + 1 < len(turf_doors):
        next_door_id = turf_doors[idx + 1]

    return render_template(
        "door.html", door=door, prev_door_id=prev_door_id, next_door_id=next_door_id
    )


@app.route("/voter/<int:id>/")
def show_voter(id):
    voter = data["voters"][id]
    return render_template("voter.html", voter=voter, dnc=is_dnc(voter))


def thing_title(obj, id):
    if obj == "turf":
        return data["turfs"][id]["desc"]
    elif obj == "door":
        return data["doors"][id]["address"]
    elif obj == "voter":
        v = data["voters"][id]
        return "{firstname} {middlename} {lastname}".format(**v)
    else:
        return "frick!! tihs is a bug"


@app.route("/<typ>/<int:id>/note/", methods=["GET", "POST"])
def note_obj(typ, id):
    assert typ in ["turf", "door", "voter"]
    obj = data[typ + "s"][id]
    if request.method == "GET":
        return render_template(
            "take_note.html",
            typ=typ,
            title=thing_title(typ, id),
            link=url_for(f"show_{typ}", id=id),
        )

    elif request.method == "POST":
        obj["notes"].insert(
            0,
            {
                "ts": datetime.datetime.now().strftime("%b %d %I:%M%P"),
                "system": False,
                "author": g.canvasser,
                "note": request.form.get("note"),
                "dnc": True if request.form.get("dnc") else False,
            },
        )
        save_data()
        return redirect(url_for(f"show_{typ}", id=id))


@app.route("/voter/<int:id>/edit/", methods=["GET", "POST"])
def edit_voter(id):
    voter = data["voters"][id]

    if request.method == "GET":
        return render_template(
            "edit_voter.html",
            voter=voter,
        )

    elif request.method == "POST":
        diffs = []
        for (
            field
        ) in "activeinactive firstname middlename lastname city cellphone landlinephone gender race birthdate".split():
            new = request.form.get(field)
            if voter[field] != new:
                diffs.append((field, voter[field], new))
                voter[field] = new

        if diffs:
            rdiffs = {}
            text = []
            for field, old, new in diffs:
                rdiffs[field] = [old, new]
                text.append(f"changed {field} from {old!r} to {new!r}.")

            voter["notes"].insert(
                0,
                {
                    "ts": datetime.datetime.now().strftime("%b %d %I:%M%P"),
                    "author": g.canvasser,
                    "system": True,
                    "note": " ".join(text),
                    "diffs": rdiffs,
                    "dnc": False,
                },
            )
            save_data()

    return redirect(url_for(f"show_voter", id=id))


if __name__ == "__main__":
    app.run(port=3030, debug=True)
