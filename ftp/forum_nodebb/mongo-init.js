// mongo-init.js
db = db.getSiblingDB('nodebb');

db.createUser({
  user: 'nodebb',
  pwd: 'nodebb123',
  roles: [
    { role: 'readWrite', db: 'nodebb' },
    { role: 'dbAdmin', db: 'nodebb' }
  ]
});

// Optionnel : créer des collections initiales
db.createCollection('users');
db.createCollection('topics');
db.createCollection('posts');
