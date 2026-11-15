//! Recognises a pointer shake: several quick left-right reversals.

/// A leg shorter than this (physical pixels) is hand tremor, not a shake.
const MIN_LEG: f64 = 60.0;
/// This many reversals inside `WINDOW_MS` make a shake.
const REVERSALS: usize = 3;
const WINDOW_MS: u64 = 700;

#[derive(Default)]
pub struct Shake {
    /// Furthest x reached in the current direction.
    extreme: Option<f64>,
    /// -1 or 1 once the pointer has travelled a full leg; 0 before that.
    direction: f64,
    reversals: Vec<u64>,
}

impl Shake {
    /// Feed one pointer sample; true once the motion so far is a shake.
    pub fn feed(&mut self, x: f64, now_ms: u64) -> bool {
        let Some(extreme) = self.extreme else {
            self.extreme = Some(x);
            return false;
        };
        if self.direction == 0.0 {
            if (x - extreme).abs() >= MIN_LEG {
                self.direction = (x - extreme).signum();
                self.extreme = Some(x);
            }
        } else if (extreme - x) * self.direction >= MIN_LEG {
            self.direction = -self.direction;
            self.extreme = Some(x);
            self.reversals.push(now_ms);
        } else if (x - extreme) * self.direction > 0.0 {
            self.extreme = Some(x);
        }
        self.reversals.retain(|at| now_ms.saturating_sub(*at) <= WINDOW_MS);
        self.reversals.len() >= REVERSALS
    }
}

#[cfg(test)]
mod tests {
    use super::Shake;

    fn shaken(samples: &[(f64, u64)]) -> bool {
        let mut shake = Shake::default();
        samples.iter().any(|(x, at)| shake.feed(*x, *at))
    }

    #[test]
    fn quick_back_and_forth_is_a_shake() {
        assert!(shaken(&[(0.0, 0), (100.0, 60), (0.0, 120), (100.0, 180), (0.0, 240)]));
    }

    #[test]
    fn a_straight_drag_is_not() {
        assert!(!shaken(&[(0.0, 0), (200.0, 60), (400.0, 120), (600.0, 180), (800.0, 240)]));
    }

    #[test]
    fn slow_reversals_and_small_jitter_are_not() {
        assert!(!shaken(&[(0.0, 0), (100.0, 500), (0.0, 1000), (100.0, 1500), (0.0, 2000)]));
        assert!(!shaken(&[(0.0, 0), (20.0, 30), (0.0, 60), (20.0, 90), (0.0, 120), (20.0, 150)]));
    }
}
