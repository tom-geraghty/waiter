#!/usr/bin/env python3
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Minimal HTML form (inline) for demonstration purposes.
# In a real-world scenario, you'd likely store templates as separate .html files.
form_html = """
<!DOCTYPE html>
<html>
  <head>
    <title>Queueing Calculator</title>
  </head>
  <body>
    <h1>Queueing Calculator</h1>
    <form method="POST" action="/">
      <p>
        <label>Your Utilisation (0.0 - 1.0):</label><br>
        <input type="number" step="0.01" name="rho_you" value="0.50" required>
      </p>
      
      <p>
        <label>Requests per Week:</label><br>
        <input type="number" step="1" name="requests_per_week" value="5" required>
      </p>
      
      <p>
        <label>Base Wait Time (hrs) at Ref Util:</label><br>
        <input type="number" step="0.01" name="base_wait_time" value="2.0" required>
      </p>
      
      <p>
        <label>Ref Util (0.0 - 1.0):</label><br>
        <input type="number" step="0.01" name="ref_util" value="0.50" required>
      </p>
      
      <p>
        <label>Cost of Delay (£ per hour):</label><br>
        <input type="number" step="0.01" name="cost_of_delay" value="100" required>
      </p>
      
      <p>
        <label>Willing to Pay for Extra Utilisation (£/week):</label><br>
        <input type="number" step="0.01" name="willing_to_pay" value="0" required>
      </p>
      
      <button type="submit">Calculate</button>
    </form>
  </body>
</html>
"""

# The results page, also inline for brevity.
result_html = """
<!DOCTYPE html>
<html>
  <head>
    <title>Queueing Calculator Results</title>
  </head>
  <body>
    <h1>Queueing Results</h1>
    <p><strong>Your Utilisation:</strong> {{ rho_you }}</p>
    <p><strong>Requests per Week:</strong> {{ requests_per_week }}</p>
    <p><strong>Base Wait Time (hrs) at Ref Util:</strong> {{ base_wait_time }}</p>
    <p><strong>Ref Util:</strong> {{ ref_util }}</p>
    <p><strong>Cost of Delay (£/hr):</strong> {{ cost_of_delay }}</p>
    <p><strong>Willing to Pay (£/week):</strong> {{ willing_to_pay }}</p>

    <hr>
    <h2>Calculated Values</h2>
    <p><strong>Wait Time (hrs/request):</strong> {{ per_request_wait }}</p>
    <p><strong>Total Delay (hrs/week):</strong> {{ total_delay }}</p>
    <p><strong>Total Delay Cost (£/week):</strong> {{ total_delay_cost }}</p>
    <p><strong>Net Trade-Off (£/week):</strong> {{ net_tradeoff }}</p>

    <hr>
    <a href="/">Back to Form</a>
  </body>
</html>
"""

@app.route("/", methods=["GET"])
def form():
    # Show the form
    return render_template_string(form_html)

@app.route("/", methods=["POST"])
def calculate():
    # 1. Parse inputs
    rho_you = float(request.form["rho_you"])
    requests_per_week = float(request.form["requests_per_week"])
    base_wait_time = float(request.form["base_wait_time"])
    ref_util = float(request.form["ref_util"])
    cost_of_delay = float(request.form["cost_of_delay"])
    willing_to_pay = float(request.form["willing_to_pay"])
    
    # 2. Calculate the wait time per request (simple ratio-based approach)
    #    wait_time = base_wait_time * ((1 - ref_util)/(1 - rho_you)) if rho_you < 1
    #    or a large fallback if rho_you == 1
    if (1 - rho_you) == 0:
        per_request_wait = 999999.9
    else:
        per_request_wait = base_wait_time * ((1 - ref_util) / (1 - rho_you))
    
    # 3. Calculate total delay and cost
    total_delay = per_request_wait * requests_per_week
    total_delay_cost = total_delay * cost_of_delay
    net_tradeoff = willing_to_pay - total_delay_cost
    
    # 4. Render results page
    return render_template_string(
        result_html,
        rho_you=rho_you,
        requests_per_week=requests_per_week,
        base_wait_time=base_wait_time,
        ref_util=ref_util,
        cost_of_delay=cost_of_delay,
        willing_to_pay=willing_to_pay,
        per_request_wait=round(per_request_wait, 2),
        total_delay=round(total_delay, 2),
        total_delay_cost=round(total_delay_cost, 2),
        net_tradeoff=round(net_tradeoff, 2)
    )

if __name__ == "__main__":
    app.run(debug=True, port=5000)
