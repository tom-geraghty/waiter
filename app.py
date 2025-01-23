#!/usr/bin/env python3
import os
from flask import Flask, request, render_template_string

app = Flask(__name__)

# -------------------------------------------------------------------
# HTML for the Form
# -------------------------------------------------------------------
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
  <h1 class="my-4">Single-Team Utilisation Calculator</h1>
  <p>See how higher utilisation affects wait times, costs, and net benefit for one team.</p>

  <form method="POST" action="/" class="row g-4">
    
    <div class="col-12 col-md-6 card">
      <label for="current_util">1) Current Team Utilisation (%)</label>
      <input type="number" step="1" id="current_util" name="current_util"
             class="form-control" placeholder="50" value="50" required>

      <label for="num_members">2) Number of Team Members</label>
      <input type="number" step="1" id="num_members" name="num_members"
             class="form-control" placeholder="5" value="5" required>

      <label for="requests_per_member">3) Avg # of Requests Each Member Makes (per week)</label>
      <input type="number" step="1" id="requests_per_member" name="requests_per_member"
             class="form-control" placeholder="4" value="4" required>

      <label for="current_wait">4) Current Average Wait Time (hours)</label>
      <input type="number" step="0.01" id="current_wait" name="current_wait"
             class="form-control" placeholder="2.0" value="2.0" required>

      <label for="cost_delay">5) Cost of Delay (£ per hour)</label>
      <input type="number" step="0.01" id="cost_delay" name="cost_delay"
             class="form-control" placeholder="100" value="100" required>
    </div>

    <div class="col-12 col-md-6 card">
      <label for="future_util">6) Desired Future Utilisation (%)</label>
      <input type="number" step="1" id="future_util" name="future_util"
             class="form-control" placeholder="80" value="80" required>

      <label for="future_value">7) Estimated Value of Higher Utilisation (£/week)</label>
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

# -------------------------------------------------------------------
# HTML for the Results
# -------------------------------------------------------------------
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
  <p>Below is your Current vs. Future utilisation breakdown, using a simple M/M/1-style ratio for waiting times.</p>

  <!-- CURRENT STATE -->
  <div class="row scenario-card">
    <h3>Current State</h3>
    <div class="col-12">
      <p><strong>Team Utilisation:</strong> {{ current_util }}%</p>
      <p><strong>Number of Team Members:</strong> {{ num_members }}</p>
      <p><strong>Requests per Member (weekly):</strong> {{ requests_per_member }}</p>
      <p><strong>Per-Request Wait Time (hrs):</strong> {{ current_wait_time }}</p>
      <p><strong>Cost of Delay (£/hr):</strong> {{ cost_delay }}</p>
    </div>
    <hr>
    <table class="summary-table">
      <tr>
        <th>Total Inter-Team Wait (hrs/week)</th>
        <td>{{ current_total_wait }}</td>
      </tr>
      <tr>
        <th>Total Delay Cost (£/week)</th>
        <td>{{ current_total_cost }}</td>
      </tr>
    </table>
  </div>

  <!-- FUTURE STATE -->
  <div class="row scenario-card">
    <h3>Future State</h3>
    <div class="col-12">
      <p><strong>Desired Future Utilisation:</strong> {{ future_util }}%</p>
      <p><strong>Estimated Value (£/week):</strong> {{ future_value }}</p>
    </div>
    <hr>
    <table class="summary-table">
      <tr>
        <th>Per-Request Wait Time (hrs)</th>
        <td>{{ future_wait_time }}</td>
      </tr>
      <tr>
        <th>Total Inter-Team Wait (hrs/week)</th>
        <td>{{ future_total_wait }}</td>
      </tr>
      <tr>
        <th>Total Delay Cost (£/week)</th>
        <td>{{ future_total_cost }}</td>
      </tr>
      <tr>
        <th>Net Best Case (Value - Future Delay Cost)</th>
        <td>{{ net_best_case }}</td>
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

# -------------------------------------------------------------------
# Flask Routes
# -------------------------------------------------------------------
app = Flask(__name__)

@app.route("/", methods=["GET"])
def show_form():
    """Display the input form."""
    return render_template_string(form_html)

@app.route("/", methods=["POST"])
def calculate():
    """Handle form submission and display queueing results."""
    # 1) Parse Inputs
    current_util = float(request.form["current_util"]) / 100.0  # Convert % to decimal
    num_members = int(request.form["num_members"])
    requests_per_member = float(request.form["requests_per_member"])
    current_wait_hrs = float(request.form["current_wait"])  # Current avg wait time (hrs)
    cost_delay_hr = float(request.form["cost_delay"])       # £ per hour of delay
    future_util = float(request.form["future_util"]) / 100.0   # Convert % to decimal
    future_value = float(request.form["future_value"])      # £/week

    # 2) Current Calculations
    # Per-request wait time is given directly => current_wait_hrs
    # Total requests per week = team_members * requests_per_member
    current_requests_week = num_members * requests_per_member
    current_total_wait = current_requests_week * current_wait_hrs
    current_total_cost = current_total_wait * cost_delay_hr

    # 3) Future Calculations
    # M/M/1 ratio approach:
    # future_wait = current_wait * [ (rho_fut / (1 - rho_fut)) / (rho_cur / (1 - rho_cur)) ]
    if (1 - current_util) == 0:
        # If current utilisation is effectively 100%, formula breaks. We'll assume extremely high wait.
        future_wait_time = 999999.9
    else:
        denom = (current_util / (1 - current_util))
        numer = (future_util / (1 - future_util)) if (1 - future_util) != 0 else 999999.9
        ratio = numer / denom
        future_wait_time = current_wait_hrs * ratio

    future_total_wait = current_requests_week * future_wait_time
    future_total_cost = future_total_wait * cost_delay_hr
    net_best_case = future_value - future_total_cost

    # 4) Render the Results
    return render_template_string(
        result_html,
        # Current
        current_util=int(request.form["current_util"]),  # show e.g. "50%"
        num_members=num_members,
        requests_per_member=int(request.form["requests_per_member"]),
        current_wait_time=round(current_wait_hrs, 2),
        cost_delay=round(cost_delay_hr, 2),
        current_total_wait=round(current_total_wait, 2),
        current_total_cost=round(current_total_cost, 2),
        # Future
        future_util=int(request.form["future_util"]),
        future_value=round(future_value, 2),
        future_wait_time=round(future_wait_time, 2),
        future_total_wait=round(future_total_wait, 2),
        future_total_cost=round(future_total_cost, 2),
        net_best_case=round(net_best_case, 2),
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
