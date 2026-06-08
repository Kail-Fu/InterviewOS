const express = require('express');
const app = express();
const usersRouter = require('./routes/users');

app.use(express.json());
app.use('/users', usersRouter);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
