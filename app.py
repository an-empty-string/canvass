import json

from flask import Flask, g, render_template, request, url_for

app = Flask(__name__)

with open("database.json") as f:
    data = json.load(f)


@app.context_processor
def inject_data():
    g.canvasser = "tris emmy wilson"
    return data


@app.route("/turf/<int:id>/")
def show_turf(id):
    turf = data["turfs"][id]
    return render_template("turf.html", turf=turf)


@app.route("/door/<int:id>/")
def show_door(id):
    door = data["doors"][id]
    return render_template("door.html", door=door)


@app.route("/voter/<int:id>/")
def show_voter(id):
    voter = data["voters"][id]
    return render_template("voter.html", voter=voter)


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
        pass


if __name__ == "__main__":
    app.run(port=3030, debug=True)
