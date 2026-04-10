# Fix Blank Graphs in Live Simulation - Approved Plan Implementation

## Plan Summary
- **Issue**: Blank PNGs saved continuously to `live_plots/step_{step}.png` due to matplotlib interactive render/save race.
- **Fix**: Data guards, longer pause, canvas flushes in `live_simulation.py`.
- **Files**: Only `live_simulation.py`.

## Steps:
- [x] Step 0: Plan created and approved ✅
- [x] Step 1: Add `os.makedirs('live_plots', exist_ok=True)` in `__init__` ✅
- [x] Step 2: In plot block (`if self.step % 10 == 0`):
  | Change |
  |--------|
  | `if not timestamps: continue` (fixes empty plots) ✅
  | `plt.pause(0.05)` + `fig.canvas.draw_idle(); plt.draw(); fig.canvas.flush_events();` ✅

  | Change |
  |--------|
  | Add `if not timestamps: continue` before plotting
  | Increase `plt.pause(0.05)`
  | After `plt.tight_layout()`: `fig.canvas.draw_idle(); plt.draw(); fig.canvas.flush_events();`
  | Keep `plt.savefig(f'live_plots/step_{self.step}.png', dpi=100, bbox_inches='tight', facecolor='white')`
- [ ] Step 3: Test: Run `python live_simulation.py` for 60+ seconds (generates step_100.png+)
- [ ] Step 4: Verify 5+ new PNGs show: black roads, colored vehicles/dots/trajectories (top-left), blue speed line (top-right), skyblue bars (bottom-left), red fill+points (bottom-right)
- [ ] Step 5: Update this TODO with results (mark complete)
- [ ] Step 6: (Optional) `rm live_plots/step_*.png` old blanks if fixed

**Test Command**: `python live_simulation.py`

**Expected**: No more blank PNGs; plots capture all 4 subplots with data after ~10 steps.

