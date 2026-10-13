
from datetime import date

from bson import ObjectId
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["beginner_db"]
todos_collection = db["todos"]


@app.route("/")
def index():
    selected_filter = request.args.get("filter", "all")

    if selected_filter not in ["all", "pending", "completed"]:
        selected_filter = "all"

    all_todos = list(todos_collection.find().sort("_id", -1))

    # Support older tasks created before completion and due dates existed.
    for todo in all_todos:
        todo["completed"] = bool(todo.get("completed", False))
        todo["due_date"] = todo.get("due_date", "")

    if selected_filter == "pending":
        todos = [todo for todo in all_todos if not todo["completed"]]
    elif selected_filter == "completed":
        todos = [todo for todo in all_todos if todo["completed"]]
    else:
        todos = all_todos

    total_count = len(all_todos)
    completed_count = sum(1 for todo in all_todos if todo["completed"])
    pending_count = total_count - completed_count

    return render_template(
        "index.html",
        todos=todos,
        selected_filter=selected_filter,
        total_count=total_count,
        completed_count=completed_count,
        pending_count=pending_count,
        today=date.today().isoformat(),
    )


@app.route("/add", methods=["POST"])
def add_todo():
    task = request.form.get("task", "").strip()
    due_date = request.form.get("due_date", "").strip()

    if task:
        todos_collection.insert_one({
            "task": task,
            "completed": False,
            "due_date": due_date,
        })

    return redirect(url_for("index"))


@app.route("/toggle/<todo_id>", methods=["POST"])
def toggle_todo(todo_id):
    if ObjectId.is_valid(todo_id):
        todo = todos_collection.find_one({"_id": ObjectId(todo_id)})

        if todo:
            current_status = bool(todo.get("completed", False))
            todos_collection.update_one(
                {"_id": ObjectId(todo_id)},
                {"$set": {"completed": not current_status}}
            )

    return redirect(url_for("index", filter=request.form.get("filter", "all")))


@app.route("/delete/<todo_id>", methods=["POST"])
def delete_todo(todo_id):
    if ObjectId.is_valid(todo_id):
        todos_collection.delete_one({"_id": ObjectId(todo_id)})

    return redirect(url_for("index", filter=request.form.get("filter", "all")))


if __name__ == "__main__":
    app.run(debug=True)