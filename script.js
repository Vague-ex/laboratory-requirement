const API_BASE = "http://127.0.0.1:8000";

async function loadItems() {
  const res = await fetch(`${API_BASE}/items`);
  const data = await res.json();
  let table = "<tr><th>Name</th><th>Qty</th><th>Cost</th></tr>";
  data.forEach(i => {
    table += `<tr><td>${i.name}</td><td>${i.quantity}</td><td>${i.unit_cost}</td></tr>`;
  });
  document.getElementById("itemsTable").innerHTML = table;
}

async function checkObsolete() {
  const res = await fetch(`${API_BASE}/audit/obsolete?threshold_qty=50&cutoff_date=2023-06-01`);
  const data = await res.json();
  alert("Obsolete Items:\n" + JSON.stringify(data, null, 2));
}
