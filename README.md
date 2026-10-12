# Lab 05: NoSQL with MongoDB

The goal of this lab is to get you comfortable with NoSQL document databases using MongoDB. You will use the `mongosh` shell to create collections, insert and query documents, and then use PyMongo to build a small Python application that talks to MongoDB Atlas. Follow the steps below to complete two case studies that show how flexible, schema-free document databases power modern applications.

> **Note:** Review and adhere to the [coding best practices](https://github.com/ksiller/DS2022/blob/main/best-practices.md) where applicable when developing your scripts. Case Study 2 should follow the same scripting and Python practices you used in [Lab 03](https://github.com/ksiller/lab-03-scripting) and [Lab 04](https://github.com/ksiller/lab-04-sql): a shebang, environment variables for credentials, functions with docstrings, comments, logging, and an `if __name__ == "__main__":` block.

## Setup

### 1. MongoDB Atlas and `mongosh`

Before you begin, set up MongoDB Atlas and connect from your environment. Follow the [MongoDB Atlas setup instructions](https://github.com/ksiller/DS2022/blob/main/setup/mongodb.md): 

- Sign up for Atlas, add the required IP access list entries, get your connection string, and save `MONGODB_ATLAS_URL`, `MONGODB_ATLAS_USER`, and `MONGODB_ATLAS_PWD` in your `~/.bashrc` (or `~/.zshrc`). 
- Install `mongosh` as described in the [mongosh install section](https://github.com/ksiller/DS2022/blob/main/setup/mongodb.md#install-the-mongosh-client-on-your-computer).

### 2. Fork and clone this repository

Fork this repository on GitHub (keep the default name): [https://github.com/ksiller/lab-05-nosql](https://github.com/ksiller/lab-05-nosql). Clone **your fork** to your own computer. Recommended location: `~/ds2022-fall-2026/lab-05-nosql`.

```bash
mkdir -p ~/ds2022-fall-2026/
cd ~/ds2022-fall-2026/
git clone https://github.com/YOUR_USERNAME/lab-05-nosql.git
```

Do all of your work in the `lab-05-nosql` directory. Commit and push deliverables to your fork, then submit the URL of the fork (see [Submit your work](#submit-your-work)).

### 3. Python environment with `uv`

Case Study 2 uses a `uv` project, as in Lab 03 and Lab 04. Confirm that `uv` is installed (`uv --version`). If that command fails, install it by following [Installing uv](https://docs.astral.sh/uv/getting-started/installation/).

From the top-level directory of your clone, create the project and add PyMongo:

```bash
cd ~/ds2022-fall-2026/lab-05-nosql
uv init --name "nosql_lab" --description "NoSQL work for DS2022"
uv add pymongo
```

- `uv init` creates `pyproject.toml`, `.python-version`, and a package directory `src/nosql_lab/` (with `__init__.py`).
- `uv add pymongo` records `pymongo` in `pyproject.toml`, writes `uv.lock` with exact versions, and installs the package into `.venv/`. Do not edit `uv.lock` by hand.

This repository already includes a `.gitignore` that excludes `.venv/`, `.vscode/`, and secret files such as `.env`. Review that file, and leave those lines in place. **Do not commit** `.venv/`. On another computer, `uv sync` recreates the environment, including `.venv`, from `pyproject.toml` and `uv.lock`.

---

## Case Study 1: The Bookstore’s New Inventory System (mongosh)

A local bookstore owner has been struggling to track authors and books on spreadsheets. They’ve heard that document databases are great for semi-structured data and want to try MongoDB.

Authors and books are a many-to-many relationship: one author can write many books, and one book can have many authors. Create two collections, `authors` and `books`.

An author document looks like this:

- `_id`: an id you choose, such as `"author_001"`
- `name`
- `nationality`
- `bio`: a subdocument embedded on the author, not a separate collection
  - `short`
  - `long`

A book document looks like this:

- `title`
- `published_year`: a year, such as `1813`
- `author_ids`: one or more author `_id` values, such as `["author_001", "author_002"]`

The starter data are in [`authors.json`](authors.json) and [`books.json`](books.json). Open `authors.json` and look through the fields.

- Jane Austen is `author_001`
- Neil Gaiman is `author_002`
- Terry Pratchett is `author_003`

Open `books.json`. The `author_ids` field lists one or more ids that match `_id` in `authors.json`.

- The book *Good Omens* (in `books.json`) lists both `author_002` and `author_003` in `author_ids`

You will load those files into new collections, list what is there, add two books of your own, and add any author those books need who is not already in the `authors` collection. When adding authors, give each one a unique `_id`, such as `"author_004"`, so it does not collide with an id that is already loaded.

### Load, extend, and query

Run the load from the repository's top-level directory so `authors.json` and `books.json` resolve in steps 3 and 4. 

1. From the repository's top-level directory, connect to MongoDB Atlas using `mongosh` and your Atlas credentials (see [Get Connection String](https://github.com/ksiller/DS2022/blob/main/setup/mongodb.md#3-get-connection-string-url) in the setup instructions). This command uses the URL and username from your environment and prompts for your password; do not put the password directly in the command.

   ```bash
   mongosh "$MONGODB_ATLAS_URL" --apiVersion 1 --username "$MONGODB_ATLAS_USER"
   ```

2. Create a new database named `bookstore`. The database is created when you first write to it. At the `mongosh` prompt, switch to it before steps 3–8:

   ```javascript
   use bookstore
   ```

3. Drop any existing `authors` collection so a second run does not insert the same authors twice. Then load `authors.json`. Each document sets `_id` to a value such as `"author_001"`. That id is reloaded with the file. MongoDB generates a hex `_id` only when you leave `_id` out. Set `_id` yourself so `books` can refer to the same author after a reload.

   ```javascript
   db.authors.drop();
   var authors = JSON.parse(fs.readFileSync("authors.json", "utf8"));
   db.authors.insertMany(authors);
   ```

4. Initialize a `books` collection with `books.json` in the same manner.

   ```javascript
   db.books.drop();
   var books = JSON.parse(fs.readFileSync("books.json", "utf8"));
   db.books.insertMany(books);
   ```

5. List every author and every book.

   ```javascript
   db.authors.find().forEach(printjson);
   db.books.find().forEach(printjson);
   ```

6. Insert two new books of your choosing. Each book needs:

   - `title`
   - `published_year` (a year such as `1999`)
   - `author_ids` with one or more author `_id` values

   An id in `author_ids` may already be in the loaded data, or it may belong to someone you are about to add. At least one author across the two books must be new, so the next step inserts at least one author. Pick a new `_id` that is not already used, such as `"author_004"`.

   For example, add one book by an existing author and one by a new author:

   ```javascript
   db.books.insertMany([
     {
       title: "The Wee Free Men",
       published_year: 2003,
       author_ids: ["author_003"],
     },
     {
       title: "Howl's Moving Castle",
       published_year: 1986,
       author_ids: ["author_004"],
     },
   ]);
   ```

7. Add every missing author of those two books. An author is missing when no document in the `authors` collection has that `_id`. MongoDB does not check that this author document exists when you save the book, so add the missing authors yourself. Each new `_id` must be unique.

   Insert each missing author with:

   - `_id`: the same id the book already stores in `author_ids`
   - `name`
   - `nationality`
   - `bio` (`short` and `long`)

   The new book above references Diana Wynne Jones as `author_004`, so add her document:

   ```javascript
   db.authors.insertOne({
     _id: "author_004",
     name: "Diana Wynne Jones",
     nationality: "British",
     bio: {
       short: "British author of fantasy novels for children and adults.",
       long: "Diana Wynne Jones was a British writer known for imaginative fantasy novels, including Howl's Moving Castle.",
     },
   });
   ```

8. Filter books by a list of authors. Include at least one author you added in step 7 and at least one author from the loaded files. A book matches when any value in `author_ids` equals an author’s `_id`. Example:

   ```javascript
   db.books
     .find({ author_ids: { $in: ["author_003", "author_004"] } })
     .forEach(printjson);
   ```

9. Save the commands from steps 3–8 in `bookstore.js` in the top-level directory of your clone, with a comment labeling each part. **Note: `use bookstore` works only at the `mongosh` prompt; inside `bookstore.js`, switch databases with `db = db.getSiblingDB("bookstore")`.** With the example books and author above, the complete file is:

   ```javascript
   // Step 2: select the bookstore database.
   db = db.getSiblingDB("bookstore");

   // Step 3: reload the starter authors.
   db.authors.drop();
   var authors = JSON.parse(fs.readFileSync("authors.json", "utf8"));
   db.authors.insertMany(authors);

   // Step 4: reload the starter books.
   db.books.drop();
   var books = JSON.parse(fs.readFileSync("books.json", "utf8"));
   db.books.insertMany(books);

   // Step 5: list all loaded authors and books.
   db.authors.find().forEach(printjson);
   db.books.find().forEach(printjson);

   // Step 6: add two books, including one by an author not in the starter data.
   db.books.insertMany([
     {
       title: "The Wee Free Men",
       published_year: 2003,
       author_ids: ["author_003"],
     },
     {
       title: "Howl's Moving Castle",
       published_year: 1986,
       author_ids: ["author_004"],
     },
   ]);

   // Step 7: add the missing author referenced by Howl's Moving Castle.
   db.authors.insertOne({
     _id: "author_004",
     name: "Diana Wynne Jones",
     nationality: "British",
     bio: {
       short: "British author of fantasy novels for children and adults.",
       long: "Diana Wynne Jones was a British writer known for imaginative fantasy novels, including Howl's Moving Castle.",
     },
   });

   // Step 8: find books by a starter-data author and the added author.
   db.books
     .find({ author_ids: { $in: ["author_003", "author_004"] } })
     .forEach(printjson);
   ```

Run `bookstore.js` from the repository's top-level directory, so `authors.json` and `books.json` are found. Connect, enter your Atlas password, then load the file:

```bash
mongosh "$MONGODB_ATLAS_URL" --apiVersion 1 --username "$MONGODB_ATLAS_USER"
```

```javascript
load("bookstore.js")
```

To run the file without staying in the shell:

```bash
mongosh "$MONGODB_ATLAS_URL" --apiVersion 1 --username "$MONGODB_ATLAS_USER" --file bookstore.js
```

**Success:** You’ve loaded a many-to-many bookstore, added books and any missing authors, and filtered books by several authors. Next, you’ll print that same join from Python.

---

## Case Study 2: Bookstore Inventory from Python (PyMongo)

The bookstore owner is impressed by the shell demo. Now they want a Python script that connects to the same Atlas cluster and prints a short report: for each author in a list, the books linked to that author, with title and publication year. This way they can eventually automate the generation of inventory reports.

**Your task:** Write a Python script that uses PyMongo to connect to MongoDB Atlas, reads the `bookstore` database from Case Study 1, and prints that joined report. Follow the scripting and Python best practices from Lab 03 and Lab 04.

### Step 1: Environment and dependencies

The `uv` project and `pymongo` dependency were created in [Setup](#3-python-environment-with-uv). If `import pymongo` fails, re-run `uv add pymongo` from the repository root.

Confirm `MONGODB_ATLAS_URL`, `MONGODB_ATLAS_USER`, and `MONGODB_ATLAS_PWD` are set in the shell you will use. If you just added them to `~/.bashrc` or `~/.zshrc`, load that file (`source ~/.bashrc` or `source ~/.zshrc`) before you run the script.

### Step 2: Write the script

Create `src/nosql_lab/bookstore_report.py` in the package directory created by `uv init --name "nosql_lab"`. The script should:

- Start with the shebang `#!/usr/bin/env python3`.
- Read `MONGODB_ATLAS_URL`, `MONGODB_ATLAS_USER`, and `MONGODB_ATLAS_PWD` as module-level variables below the imports (outside `main`), the same way Lab 03 reads `GITHUB_USER`. **Do not hardcode credentials.**
- Give every function a docstring, and add comments in the code.
- Use `logging` to report status (connection success and errors). `print` is fine inside `main` for the report itself.
- Wrap the code that opens, uses, and closes the MongoDB client in a `try`/`except` block, and close the client when you are done.
- Define a `main` function that:
  - Connects to MongoDB Atlas with `pymongo.MongoClient`, passing the connection URL and the username and password from the environment variables.
  - Selects the `bookstore` database and the `authors` and `books` collections.
  - Uses a list of author `_id` values that includes at least one author you added in step 7 and at least one author from the loaded files.
  - Prints the total number of authors in that list. Then, for each author, prints the author name and, under that name, each linked book’s title and publication year (`published_year`). A co-authored book appears under each of its authors. Format the output so it is easy to read.
- Call `main()` from an `if __name__ == "__main__":` block so it runs only when the file is executed directly. See [class/03-scripting](https://github.com/ksiller/DS2022/blob/main/class/03-scripting/README.md) for how that guard works.

For a list that includes `author_002`, `author_003`, and one author you added, the report should look like this. Your own author and books will differ. *Good Omens* is listed under both of its authors.

```text
Authors: 3

Neil Gaiman
  Good Omens (1990)
  American Gods (2001)

Terry Pratchett
  Good Omens (1990)
  The Colour of Magic (1983)

Your Author
  Your New Book (1999)
```

Run the script from the repository root with `uv run`, so Python uses the project environment. Confirm that it connects to Atlas and prints the report from the documents you added in Case Study 1:

```bash
uv run python src/nosql_lab/bookstore_report.py
```

**Hint:** Use `count_documents` for the number of authors in your list. Resolve each author’s books from `author_ids` on the book, not from a second hardcoded list of titles. `books.find({ "author_ids": author["_id"] })` returns every book that lists that author’s `_id`. Print `title` and `published_year` for each one.

For the lookup in Python, see the scripts in [Class 05: NoSQL](https://github.com/ksiller/DS2022/tree/main/class/05-nosql). [`08-mongo_join.py`](https://github.com/ksiller/DS2022/blob/main/class/05-nosql/08-mongo_join.py) finds a comment by `movie_id`, then loads the movie with that `_id`. Use the same idea: `author_ids` on a book holds an author’s `_id`. [`09-mongo_embed.py`](https://github.com/ksiller/DS2022/blob/main/class/05-nosql/09-mongo_embed.py) shows the other pattern, nesting related data inside one document. Your author `bio` is already embedded; the report should join.

**Success:** You’ve connected to the same MongoDB data from Python and printed, for each author, the title and publication year of each linked book. That’s the same pattern used in larger systems: shell for ad hoc operations, Python (or another driver) for automation and applications.

---

## Learning Outcomes

By completing this lab, you have:

- Used the MongoDB shell (`mongosh`) to load documents, insert them, and query across collections.
- Stored a many-to-many relationship by setting each author’s `_id` to a value such as `"author_001"` and listing those ids in `author_ids` on books, and embedded `bio` on the author instead of storing a `bio_id`.
- Filtered books by a list of authors and captured those shell commands in a script file.
- Created a reproducible Python environment with `uv` and installed PyMongo into it.
- Connected to MongoDB Atlas from Python with PyMongo and environment variables.
- Written a script that follows scripting best practices (shebang, docstrings, comments, logging, and an entry-point guard) and, for each author, prints the title and publication year of each linked book.

These skills translate directly to real-world use: document stores like MongoDB are common in data pipelines, APIs, and applications where nested data and references between documents are both useful.

---

## Submit your work

Your repository should look roughly like this (other `uv init` files are fine too):

```text
lab-05-nosql/
├── .gitignore
├── README.md
├── authors.json
├── books.json
├── bookstore.js
├── pyproject.toml
├── uv.lock
└── src/
    └── nosql_lab/
        ├── __init__.py
        └── bookstore_report.py
```

**Submission steps**

Confirm that `.venv` and `.vscode` are listed in `.gitignore`, then run `git status` and verify that `.venv/` and `.vscode/` are **not** staged for commit.

Add all project files (gitignored paths stay out automatically):

```bash
git add .
```

Commit your work:

```bash
git commit -m "Complete Lab 05: NoSQL with MongoDB"
```

Push to your repository:

```bash
git push origin main
```

Submit the URL of your forked repository in the Canvas assignment. The URL should look like: `https://github.com/YOUR_USERNAME/lab-05-nosql`
