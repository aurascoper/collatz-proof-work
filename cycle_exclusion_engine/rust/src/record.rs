//! NDJSON record matching `shared/FORMAT.md`.

use serde::{Deserialize, Serialize};

use crate::affine::ParityBlock;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParityBlockRecord {
    pub mask_le_hex: String,
    pub K: u32,
    pub m: u32,
    pub S: u32,
    pub A_dec: String,
    pub B_dec: String,
    pub denom_dec: String,
    pub is_self_loop_candidate: bool,
    pub label: Option<String>,
}

impl From<&ParityBlock> for ParityBlockRecord {
    fn from(pb: &ParityBlock) -> Self {
        Self {
            mask_le_hex: format!("0x{:x}", pb.mask_le),
            K: pb.k,
            m: pb.m,
            S: pb.s,
            A_dec: pb.a.to_str_radix(10),
            B_dec: pb.b.to_str_radix(10),
            denom_dec: pb.denom.to_str_radix(10),
            is_self_loop_candidate: true,
            label: None,
        }
    }
}
