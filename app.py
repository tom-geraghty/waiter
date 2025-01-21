#!/usr/bin/env python3
import os
from flask import Flask, request, render_template_string

app = Flask(__name__)

# HTML form for two scenarios: Current State and Future State
form_html = """
<!DOCTYPE html>
<html>
  <head>
    <title>Queueing Calculator - Compare Current & Future</title>
    <style>
      body { font-family: sans-serif; }
      h1, h2 { margin-bottom: 0.5em; }
      .scenario-box {
        border: 1px solid #ccc; 
        padding: 1em; 
        margin: 1em 0;
      }
      label { font-weight: bold; }
      input { width: 100px; }
    </style>
  </head>
  <body>
    <h1>Compare Current & Future States</h1>
    <form method="POST" action="/">
      
      <div class="scenario-box">
        <h2>Current State</h2>
        <p>
          <label>Your Utilisation (0.0 - 1.0):</label><br>
          <input type="number" step="0.01" name="rho_you_cur" value="0.50" required>
        </p>
        <p>
          <label>Requests per Week:</label><br>
          <input type="number" step="1" name="requests_cur" value="5" required>
        </p>
        <p>
          <label>Base Wait Time (hrs) at Ref Util:</label><br>
          <input type="number" step="0.01" name="base_wait_time_cur" value="2.0" required>
        </p>
        <p>
          <label>Ref Util (0.0 - 1.0):</label><br>
          <input type="number" step="0.01" name="ref_util_cur" value="0.50" required>
        </p>
        <p>
          <label>Cost of Delay (£ per hour):</label><br>
          <input type="number" step="0.01" name="cost_of_delay_cur" value="100" required>
        </p>
        <p>
          <label>Willing to Pay (£/week):</label><br>
          <input type="number" step="0.01" name="willing_to_pay_cur" value="0" required>
        </p>
      </div>
      
      <div class="scenario-box">
        <h2>Future State</h2>
        <p>
          <label>Your Utilisation (0.0 - 1.0):</label><br>
          <input type="number" step="0.01" name="rho_you_fut" value="0.90" required>
        </p>
        <p>
          <label>Requests per Week:</label><br>
          <input type="number" step="1" name="requests_fut" value="5" required>
        </p>
        <p>
          <label>Base Wait Time (hrs) at Ref Util:</label><br>
          <input type="number" step="0.01" name="base_wait_time_fut" value="2.0" required>
        </p>
        <p>
          <label>Ref Util (0.0 - 1.0):</label><br>
          <input type="number" step="0.01" name="ref_util_fut" value="0.50" required>
        </p>
        <p>
          <label>Cost of Delay (£ per hour):</label><br>
          <input type="number" step="0.01" name="cost_of_delay_fut" value="100" required>
        </p>
        <p>
          <label>Willing to Pay (£/week):</label><br>
          <input type="number" step="0.01" name="willing_to_pay_fut" value="500" required>
        </p>
      </div>
      
      <button type="submit">Calculate Both</button>
    </form>
  </body>
</html>
"""

# Results page: shows side-by-side comparison of Current State & Future State
result_html = """
<!DOCTYPE html>
<html>
  <head>
    <title>Queueing Comparison Results</title>
    <style>
      body { font-family: sans-serif; }
      .scenario-table {
        display: table;
        width: 100%%;
        border-collapse: collapse;
        margin-bottom: 2em;
      }
      .scenario-row { display: table-row; }
      .scenario-cell {
        display: table-cell;
        vertical-align: top;
        border: 1px solid #ccc;
        padding: 1em;
        width: 50%%;
      }
      h2 { margin-top: 0; }
    </style>
  </head>
  <body>
    <h1>Comparison of Current vs. Future State</h1>
    
    <div class="scenario-table">
      <div class="scenario-row">
        <div class="scenario-cell">
          <h2>Current State</h2>
          <p><strong>Your Utilisation:</strong> {{ rho_you_cur }}</p>
          <p><strong>Requests/Week:</strong> {{ requests_cur }}</p>
          <p><strong>Base Wait Time:</strong> {{ base_wait_time_cur }} hrs (Ref Util: {{ ref_util_cur }})</p>
          <p><strong>Cost of Delay:</strong> £{{ cost_of_delay_cur }}/hr</p>
          <p><strong>Willing to Pay:</strong> £{{ willing_to_pay_cur }}/week</p>
          <hr>
          <h3>Results</h3>
          <p><strong>Per-Request Wait Time:</strong> {{ wait_cur }} hrs</p>
          <p><strong>Total Delay:</strong> {{ delay_cur }} hrs/week</p>
          <p><strong>Total Delay Cost:</strong> £{{ cost_cur }}/week</p>
          <p><strong>Net Trade-Off:</strong> £{{ net_cur }}/week</p>
        </div>
        <div class="scenario-cell">
          <h2>Future State</h2>
          <p><strong>Your Utilisation:</strong> {{ rho_you_fut }}</p>
          <p><strong>Requests/Week:</strong> {{ requests_fut }}</p>
          <p><strong>Base Wait Time:</strong> {{ base_wait_time_fut }} hrs (Ref Util: {{ ref_util_fut }})</p>
          <p><strong>Cost of Delay:</strong> £{{ cost_of_delay_fut }}/hr</p>
          <p><strong>Willing to Pay:</strong> £{{ willing_to_pay_fut }}/week</p>
          <hr>
          <h3>Results</h3>
          <p><strong>Per-Request Wait Time:</strong> {{ wait_fut }} hrs</p>
          <p><strong>Total Delay:</strong> {{ delay_fut }} hrs/week</p>
          <p><strong>Total Delay Cost:</strong> £{{ cost_fut }}/week</p>
          <p><strong>Net Trade-Off:</strong> £{{ net_fut }}/week</p>
        </div>
      </div>
    </div>
    
    <a href="/">Back to Form</a>
  </body>
</html>
"""

app = Flask(__name__)

@app.route("/", methods=["GET"])
def form():
    """Show a single form with fields for both Current and Future states."""
    return render_template_string(form_html)

@app.route("/", methods=["POST"])
def calculate():
    """Calculate queueing metrics for both scenarios and display them."""
    # --- Current State ---
    rho_you_cur = float(request.form["rho_you_cur"])
    requests_cur = float(request.form["requests_cur"])
    base_wait_time_cur = float(request.form["base_wait_time_cur"])
    ref_util_cur = float(request.form["ref_util_cur"])
    cost_of_delay_cur = float(request.form["cost_of_delay_cur"])
    willing_to_pay_cur = float(request.form["willing_to_pay_cur"])
    
    # Calculate wait time for current scenario
    if (1 - rho_you_cur) == 0:
        wait_cur = 999999.9
    else:
        wait_cur = base_wait_time_cur * ((1 - ref_util_cur) / (1 - rho_you_cur))
    
    delay_cur = wait_cur * requests_cur
    cost_cur = delay_cur * cost_of_delay_cur
    net_cur = willing_to_pay_cur - cost_cur

    # --- Future State ---
    rho_you_fut = float(request.form["rho_you_fut"])
    requests_fut = float(request.form["requests_fut"])
    base_wait_time_fut = float(request.form["base_wait_time_fut"])
    ref_util_fut = float(request.form["ref_util_fut"])
    cost_of_delay_fut = float(request.form["cost_of_delay_fut"])
    willing_to_pay_fut = float(request.form["willing_to_pay_fut"])
    
    # Calculate wait time for future scenario
    if (1 - rho_you_fut) == 0:
        wait_fut = 999999.9
    else:
        wait_fut = base_wait_time_fut * ((1 - ref_util_fut) / (1 - rho_you_fut))
    
    delay_fut = wait_fut * requests_fut
    cost_fut = delay_fut * cost_of_delay_fut
    net_fut = willing_to_pay_fut - cost_fut

    # Render results
    return render_template_string(
        result_html,
        # Current scenario
        rho_you_cur=rho_you_cur,
        requests_cur=requests_cur,
        base_wait_time_cur=base_wait_time_cur,
        ref_util_cur=ref_util_cur,
        cost_of_delay_cur=cost_of_delay_cur,
        willing_to_pay_cur=willing_to_pay_cur,
        
        wait_cur=round(wait_cur, 2),
        delay_cur=round(delay_cur, 2),
        cost_cur=round(cost_cur, 2),
        net_cur=round(net_cur, 2),

        # Future scenario
        rho_you_fut=rho_you_fut,
        requests_fut=requests_fut,
        base_wait_time_fut=base_wait_time_fut,
        ref_util_fut=ref_util_fut,
        cost_of_delay_fut=cost_of_delay_fut,
        willing_to_pay_fut=willing_to_pay_fut,
        
        wait_fut=round(wait_fut, 2),
        delay_fut=round(delay_fut, 2),
        cost_fut=round(cost_fut, 2),
        net_fut=round(net_fut, 2)
    )

if __name__ == "__main__":
    # For local testing; Render will use a Start Command (gunicorn, etc.)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
