// Step 2: select the bookstore database.
db = db.getSiblingDB("bookstore");

// Step 3: reload the starter authors so the script can be rerun safely.
db.authors.drop();
var authors = JSON.parse(fs.readFileSync("authors.json", "utf8"));
db.authors.insertMany(authors);

// Step 4: reload the starter books so the script can be rerun safely.
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

// Step 8: find books by an author from the starter data and the added author.
db.books
  .find({ author_ids: { $in: ["author_003", "author_004"] } })
  .forEach(printjson);
