const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const Reviews = require('./review');
const Dealerships = require('./dealership');
const app = express();
app.use(cors());
app.use(express.json({limit: '32kb'}));
app.set('json spaces', 2);
const route = handler => (req, res, next) => Promise.resolve(handler(req, res)).catch(next);
const numericId = value => { const id = Number(value); if (!Number.isSafeInteger(id) || id < 1) { const e = new Error('Invalid dealer id'); e.status = 400; throw e; } return id; };
app.get('/', (req, res) => res.json({service: 'Best Cars Express-Mongo API', status: 'ok'}));
app.get('/health', route(async (req, res) => res.status(mongoose.connection.readyState === 1 ? 200 : 503).json({database: mongoose.connection.readyState === 1 ? 'connected' : 'disconnected'})));
app.get('/fetchReviews', route(async (req, res) => res.json(await Reviews.find().select('-_id -__v').sort({id: 1}))));
app.get('/fetchReviews/dealer/:id', route(async (req, res) => res.json(await Reviews.find({dealership: numericId(req.params.id)}).select('-_id -__v').sort({id: -1}))));
app.get('/fetchDealers', route(async (req, res) => res.json(await Dealerships.find().select('-_id -__v').sort({id: 1}))));
app.get('/fetchDealers/:state', route(async (req, res) => res.json(await Dealerships.find(req.params.state === 'All' ? {} : {state: req.params.state}).select('-_id -__v').sort({id: 1}))));
app.get('/fetchDealer/:id', route(async (req, res) => res.json(await Dealerships.find({id: numericId(req.params.id)}).select('-_id -__v'))));
const counterSchema = new mongoose.Schema({_id: String, sequence: Number});
const Counter = mongoose.model('counters', counterSchema);
app.post('/insert_review', route(async (req, res) => {
  const data = req.body;
  const dealerId = numericId(data.dealership);
  if (!await Dealerships.exists({id: dealerId})) return res.status(404).json({error: 'Dealer not found'});
  const counter = await Counter.findOneAndUpdate({_id: 'reviews'}, {$inc: {sequence: 1}}, {new: true});
  const review = new Reviews({id: counter.sequence, name: data.name, dealership: dealerId, review: data.review, purchase: data.purchase, purchase_date: data.purchase_date, car_make: data.car_make, car_model: data.car_model, car_year: data.car_year});
  await review.save();
  const output = review.toObject(); delete output._id; delete output.__v;
  res.status(201).json(output);
}));
app.use((error, req, res, next) => {
  const status = error.status || (error.name === 'ValidationError' || error instanceof SyntaxError ? 400 : 500);
  res.status(status).json({error: status < 500 ? error.message : 'Database request failed'});
});
async function start() {
  await mongoose.connect(process.env.MONGODB_URL || 'mongodb://127.0.0.1:27017/dealershipsDB', {serverSelectionTimeoutMS: 15000});
  const read = file => JSON.parse(fs.readFileSync(path.join(__dirname, 'data', file), 'utf8'));
  if (!await Dealerships.exists({})) await Dealerships.insertMany(read('dealerships.json').dealerships);
  if (!await Reviews.exists({})) await Reviews.insertMany(read('reviews.json').reviews);
  const last = await Reviews.findOne().sort({id: -1});
  await Counter.updateOne({_id: 'reviews'}, {$max: {sequence: last ? last.id : 0}}, {upsert: true});
  return app.listen(Number(process.env.PORT || 3030), '0.0.0.0', () => console.log('Express-Mongo API ready on port ' + (process.env.PORT || 3030)));
}
if (require.main === module) start().catch(error => { console.error(error.message); process.exit(1); });
module.exports = {app, start};
