db = db.getSiblingDB("nodebb");

db.createUser({
  user: "nodebb",
  pwd: "nodebb",
  roles: [{ role: "readWrite", db: "nodebb" }]
});

