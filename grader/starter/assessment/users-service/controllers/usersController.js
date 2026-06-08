const fs = require('fs');
const path = require('path');
const usersPath = path.join(__dirname, '../db/users.json');

function getUsers(req, res) {
  const data = JSON.parse(fs.readFileSync(usersPath, 'utf8'));
  res.json(data);
}

function getUserById(req, res) {
  const data = JSON.parse(fs.readFileSync(usersPath, 'utf8'));
  const user = data.find(u => u.id === req.params.id);
  if (user) {
    res.json(user);
  } else {
    res.status(404).json({ error: 'User not found' });
  }
}

module.exports = { getUsers, getUserById };
