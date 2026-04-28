//! `cee_periodic_generate` -- Iteration 072 periodic-word generator.
//!
//! Enumerates primitive cyclically-admissible periodic parity words of
//! length T in [t_min, t_max], composes their exact affine maps, and
//! emits NDJSON v2 records (one canonical representative per rotation
//! class).
//!
//! Usage:
//!   cee_periodic_generate --t-min 1 --t-max 12 --output periodic_T12.ndjson
//!   cee_periodic_generate --t-min 1 --t-max 24 --primitive-only false --output all.ndjson

use std::env;
use std::fs::File;
use std::io::{BufWriter, Write};
use std::time::Instant;

use cee_rust::{
    affine_periodic::{compose_affine_periodic, denom_from},
    canonical_periodic::{canonical_rotation_msb, to_bit_string},
    periodic::{enumerate_cyclically_admissible, is_primitive},
    ndjson_periodic::PeriodicNdjsonRecord,
};

fn parse_args() -> (usize, usize, bool, String) {
    let args: Vec<String> = env::args().collect();
    let mut t_min = 1usize;
    let mut t_max = 12usize;
    let mut primitive_only = true;
    let mut output: Option<String> = None;
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--t-min" => { t_min = args[i+1].parse().expect("t-min usize"); i += 2; }
            "--t-max" => { t_max = args[i+1].parse().expect("t-max usize"); i += 2; }
            "--primitive-only" => {
                primitive_only = args[i+1].parse().unwrap_or(true);
                i += 2;
            }
            "--output" | "-o" => { output = Some(args[i+1].clone()); i += 2; }
            "--help" | "-h" => {
                eprintln!("usage: cee_periodic_generate --t-min N --t-max N \
                           [--primitive-only true|false] --output PATH");
                std::process::exit(0);
            }
            other => {
                eprintln!("unknown arg: {}", other);
                std::process::exit(2);
            }
        }
    }
    let output = output.expect("--output required");
    (t_min, t_max, primitive_only, output)
}

fn main() -> std::io::Result<()> {
    let (t_min, t_max, primitive_only, output) = parse_args();
    eprintln!("[072] t_min={} t_max={} primitive_only={} output={}",
              t_min, t_max, primitive_only, output);

    let f = File::create(&output)?;
    let mut w = BufWriter::with_capacity(1 << 20, f);

    let t0 = Instant::now();
    let mut total_emitted: u64 = 0;
    let mut total_seen: u64 = 0;
    let mut total_canonical: u64 = 0;

    for t in t_min..=t_max {
        let words = enumerate_cyclically_admissible(t);
        let words_seen = words.len() as u64;
        let mut canon_count: u64 = 0;
        let mut emit_count: u64 = 0;
        for word in words {
            // Take only the canonical representative of each rotation class.
            let (canon, shift) = canonical_rotation_msb(word, t);
            if canon != word {
                continue;
            }
            canon_count += 1;
            let primitive = is_primitive(word, t);
            if primitive_only && !primitive {
                continue;
            }
            let bits = to_bit_string(word, t);
            let canon_bits = to_bit_string(canon, t);
            let (a, b, m, s) = compose_affine_periodic(word, t);
            let denom = denom_from(&a, s);
            let rec = PeriodicNdjsonRecord {
                word_bits: bits,
                T: t as u32,
                m: m as u32,
                S: s as u32,
                A_str: a.to_str_radix(10),
                B_str: b.to_str_radix(10),
                denom_str: denom.to_str_radix(10),
                primitive,
                cyclic_admissible: true,
                canonical_rotation: canon_bits,
                rotation_index: shift as u32,
            };
            serde_json::to_writer(&mut w, &rec).expect("ndjson write");
            w.write_all(b"\n")?;
            emit_count += 1;
        }
        eprintln!("  T={:>3}  cyclic_adm_words={:>10}  canonical={:>10}  emitted={:>10}",
                  t, words_seen, canon_count, emit_count);
        total_seen += words_seen;
        total_canonical += canon_count;
        total_emitted += emit_count;
    }
    w.flush()?;
    let elapsed = t0.elapsed().as_secs_f64();
    eprintln!("[072] total: seen={}  canonical={}  emitted={}  ({:.2}s, {:.2}e3 emit/s)",
              total_seen, total_canonical, total_emitted, elapsed,
              total_emitted as f64 / elapsed / 1e3);
    Ok(())
}
