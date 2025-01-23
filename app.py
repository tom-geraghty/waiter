#!/usr/bin/env python3
import os
from flask import Flask, request, render_template_string

app = Flask(__name__)

# ---------------------------
# 1) The HTML Form
# ---------------------------
form_html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Team Utilisation Calculator</title>
  <!-- Bootstrap 5 (CDN) -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { margin: 20px; }
    .card {
      margin-bottom: 1.5rem;
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 1rem;
    }
    label { font-weight: 500; margin-top: 0.5rem; }
  </style>
</head>
<body>
<div class="container">
  <h1 class="my-4">Team Utilisation Calculator</h1>
  <p>See how higher utilisation affects wait times, costs, and net benefit for a single team.</p>

  <form method="POST" action="/" class="row g-4">
    <div class="col-12 col-md-6 card">
      <label for="current_util">Current Team Utilisation (%)</label>
      <input type="number" step="1" id="current_util" name="current_util"
             class="form-control" placeholder="50" value="50" required>

      <label for="num_members">Number of Team Members</label>
      <input type="number" step="1" id="num_members" name="num_members"
             class="form-control" placeholder="5" value="5" required>

      <label for="requests_per_member">Avg Requests per Member per Week</label>
      <input type="number" step="1" id="requests_per_member" name="requests_per_member"
             class="form-control" placeholder="4" value="4" required>

      <label for="current_wait">Current Average Wait Time (hours)</label>
      <input type="number" step="0.01" id="current_wait" name="current_wait"
             class="form-control" placeholder="2.0" value="2.0" required>

      <label for="cost_delay">Cost of Delay (£ per hour)</label>
      <input type="number" step="0.01" id="cost_delay" name="cost_delay"
             class="form-control" placeholder="100" value="100" required>
    </div>

    <div class="col-12 col-md-6 card">
      <label for="future_util">Desired Future Utilisation (%)</label>
      <input type="number" step="1" id="future_util" name="future_util"
             class="form-control" placeholder="80" value="80" required>

      <label for="future_value">Estimated Value of Higher Utilisation (£/week)</label>
      <input type="number" step="0.01" id="future_value" name="future_value"
             class="form-control" placeholder="500" value="500" required>
    </div>

    <div class="col-12 text-end">
      <button type="submit" class="btn btn-primary btn-lg">Calculate</button>
    </div>
  </form>
</div>
</body>
</html>
"""

# ---------------------------
# 2) The Results Page
# ---------------------------
result_html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Utilisation Results</title>
  <!-- Bootstrap 5 -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { margin: 20px; }
    .scenario-card {
      border: 1px solid #ddd;
      padding: 1rem;
      border-radius: 8px;
      margin-bottom: 2rem;
    }
    .scenario-card h3 { margin-top: 0.5rem; }
    .summary-table {
      width: 100%%;
      border-collapse: collapse;
      margin-top: 1rem;
    }
    .summary-table th, .summary-table td {
      border: 1px solid #ccc;
      padding: 0.75rem;
      text-align: left;
    }
  </style>
</head>
<body>
<div class="container">
  <h1 class="my-4">Team Utilisation Results</h1>
  <p>Here is your current vs. future utilisation breakdown.</p>

  <!-- CURRENT STATE -->
  <div class="row scenario-card">
    <h3>Current State</h3>
    <div class="col-12">
      <p><strong>Team Utilisation:</strong> {{ current_util }}%</p>
      <p><strong>Number of Team Members:</strong> {{ num_members }}</p>
      <p><strong>Requests per Member:</strong> {{ requests_per_member }}</p>
      <p><strong>Per-Request Wait Time (hrs):</strong> {{ current_wait_time }}</p>
      <p><strong>Cost of Delay (per hour):</strong> £{{ cost_delay }}</p>
    </div>
    <hr>
    <table class="summary-table">
      <tr>
        <th>Current Total Inter-Team Wait Time (hrs/week)</th>
        <td>{{ current_total_wait }}</td>
      </tr>
      <tr>
        <th>Current Total Delay Cost (£/week)</th>
        <td>{{ current_total_cost }}</td>
      </tr>
    </table>
  </div>

  <!-- FUTURE STATE -->
  <div class="row scenario-card">
    <h3>Future State</h3>
    <div class="col-12">
      <p><strong>Desired Future Utilisation:</strong> {{ future_util }}%</p>
      <p><strong>Estimated Extra Value (per week):</strong> £{{ future_value }}</p>
    </div>
    <hr>
    <table class="summary-table">
      <tr>
        <th>Future Per-Request Wait Time (hrs)</th>
        <td>{{ future_wait_time }}</td>
      </tr>
      <tr>
        <th>Future Total Inter-Team Wait Time (hrs/week)</th>
        <td>{{ future_total_wait }}</td>
      </tr>
      <tr>
        <th>Future Total Delay Cost (£/week)</th>
        <td>{{ future_total_cost }}</td>
      </tr>
      <tr>
        <th>Net "Best Case" (Value - Future Delay Cost)</th>
        <td>£{{ net_best_case }}</td>
      </tr>
    </table>
  </div>

  <div class="text-end">
    <a href="/" class="btn btn-secondary">Back to Form</a>
  </div>
</div>
</body>
</html>
"""

# ---------------------------
# 3) Flask Routes
# ---------------------------
@app.route("/", methods=["GET"])
def show_form():
    """Renders the form for entering current/future utilisation data."""
    return render_template_string(form_html)

@app.route("/", methods=["POST"])
def calculate():
    """Handles form submission, calculates queueing metrics, and displays results."""
    # Parse form inputs
    current_util = float(request.form["current_util"]) / 100.0  # convert % to decimal
    num_members = int(request.form["num_members"])
    requests_per_member = float(request.form["requests_per_member"])
    current_wait_hrs = float(request.form["current_wait"])
    cost_delay_hr = float(request.form["cost_delay"])  # cost of delay per hour
    future_util = float(request.form["future_util"]) / 100.0    # convert % to decimal
    future_value = float(request.form["future_value"])

    # --- CURRENT CALCULATIONS ---
    # Per-request wait time = current_wait_hrs (directly from user)
    # Total requests = num_members * requests_per_member
    current_total_requests = num_members * requests_per_member
    current_total_wait = current_total_requests * current_wait_hrs
    current_total_cost = current_total_wait * cost_delay_hr

    # --- FUTURE CALCULATIONS ---
    # We'll scale the wait time from current to future using a ratio-based approach
    # future_wait_time = current_wait_time * [(1 - future_util) / (1 - current_util)]
    if (1 - current_util) == 0:
        # If current_util is 100%, formula breaks. We'll assume extremely high wait.
        future_wait_time = 999999.9
    else:
        future_wait_time = current_wait_hrs * ((1 - future_util) / (1 - current_util))

    future_total_requests = current_total_requests  # same # of requests, unless you want to adjust
    future_total_wait = future_total_requests * future_wait_time
    future_total_cost = future_total_wait * cost_delay_hr

    net_best_case = future_value - future_total_cost

    # Render results using the second HTML template
    return render_template_string(
        result_html,
        current_util=int(request.form["current_util"]),  # show as int
        num_members=num_members,
        requests_per_member=int(request.form["requests_per_member"]),
        current_wait_time=round(current_wait_hrs, 2),
        cost_delay=round(cost_delay_hr, 2),
        current_total_wait=round(current_total_wait, 2),
        current_total_cost=round(current_total_cost, 2),

        future_util=int(request.form["future_util"]),
        future_value=round(future_value, 2),
        future_wait_time=round(future_wait_time, 2),
        future_total_wait=round(future_total_wait, 2),
        future_total_cost=round(future_total_cost, 2),
        net_best_case=round(net_best_case, 2)
    )

if __name__ == "__main__":
    # For local development:
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
