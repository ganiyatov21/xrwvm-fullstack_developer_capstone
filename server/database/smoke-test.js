const assert = require('node:assert/strict');
const base = process.env.API_URL || 'http://localhost:3030';
async function request(path, options) {
  const response = await fetch(base + path, options);
  assert.ok(response.ok, `HTTP ${response.status}: ${path}`);
  return response.json();
}
(async () => {
  const dealers = await request('/fetchDealers');
  assert.ok(dealers.length > 0);
  const kansas = await request('/fetchDealers/Kansas');
  assert.ok(kansas.length > 0);
  assert.ok(kansas.every(dealer => dealer.state === 'Kansas'));
  const detail = await request('/fetchDealer/1');
  assert.equal(detail[0].id, 1);
  const review = {name:'Integration Driver', dealership:1, review:'Excellent service and a wonderful car!', purchase:true, purchase_date:'2023-06-15', car_make:'Toyota', car_model:'Camry', car_year:2023};
  const saved = await request('/insert_review', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(review)});
  const reviews = await request('/fetchReviews/dealer/1');
  assert.ok(reviews.some(item => item.id === saved.id && item.review === review.review));
  assert.equal((await fetch(base+'/fetchDealer/invalid')).status, 400);
  console.log('PASS: dealer listing, Kansas filter, details, review persistence, invalid IDs');
})().catch(error => {console.error(error); process.exit(1);});
