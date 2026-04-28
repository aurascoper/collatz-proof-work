//! NDJSON v2 record per Iteration 072 spec.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[allow(non_snake_case)]
pub struct PeriodicNdjsonRecord {
    pub word_bits: String,
    pub T: u32,
    pub m: u32,
    pub S: u32,
    pub A_str: String,
    pub B_str: String,
    pub denom_str: String,
    pub primitive: bool,
    pub cyclic_admissible: bool,
    pub canonical_rotation: String,
    pub rotation_index: u32,
}
