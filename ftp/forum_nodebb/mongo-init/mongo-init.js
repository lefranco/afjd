// Initialisation simple
db.createUser({
  user: 'nodebb',
  pwd: 'nodebbpassword123',
  roles: [
    { role: 'readWrite', db: 'nodebb' },
    { role: 'dbAdmin', db: 'nodebb' }
  ]
});
