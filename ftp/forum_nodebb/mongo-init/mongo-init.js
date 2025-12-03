db = db.getSiblingDB('admin');

db.auth('admin', 'admin123');

db = db.getSiblingDB('nodebb');

db.createUser({
  user: 'nodebb',
  pwd: 'nodebb123',
  roles: [
    { role: 'readWrite', db: 'nodebb' },
    { role: 'dbAdmin', db: 'nodebb' }
  ]
});

print('MongoDB initialized for NodeBB');
