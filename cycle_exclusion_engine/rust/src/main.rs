//! `cee_generate` -- CLI: enumerate admissible parity blocks of length K,
//! compose their affine maps, write NDJSON to stdout (or --out file).
//! Reports throughput on stderr.
//!
//! Usage:
//!   cargo run --release --bin cee_generate -- --K 8
//!   cargo run --release --bin cee_generate -- --K 12 --out blocks_K12.ndjson
//!   cargo run --release --bin cee_generate -- --K 24 --benchmark
//!
//! `--benchmark` skips the writer and only measures generation+composition
//! throughput.

use std::time::Instant;
use std::env;

use cee_rust::{AdmissibleParityIter, ParityBlock, ParityBlockRecord, NdjsonWriter, parity};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    let mut k: u32 = 8;
    let mut out_path: Option<String> = None;
    let mut benchmark = false;
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--K" | "-k" => { k = args[i+1].parse()?; i += 2; }
            "--out" | "-o" => { out_path = Some(args[i+1].clone()); i += 2; }
            "--benchmark" | "-b" => { benchmark = true; i += 1; }
            "--help" | "-h" => {
                eprintln!("usage: cee_generate --K <K> [--out file] [--benchmark]");
                return Ok(());
            }
            other => {
                eprintln!("unknown arg: {}", other);
                std::process::exit(2);
            }
        }
    }

    eprintln!("[cee_generate] K={}  expected count = F_{} = {}",
              k, k + 2, parity::count_admissible(k));

    let t0 = Instant::now();
    let mut count: u64 = 0;
    let mut compose_total_ns: u128 = 0;
    let mut write_total_ns: u128 = 0;
    use std::io::{BufWriter, Write};
    let mut writer: Option<NdjsonWriter<Box<dyn Write>>> =
        if let Some(p) = out_path.as_deref() {
            let f = std::fs::File::create(p)?;
            let bw: Box<dyn Write> = Box::new(BufWriter::with_capacity(1 << 20, f));
            Some(NdjsonWriter::new(bw))
        } else if benchmark {
            None
        } else {
            let bw: Box<dyn Write> = Box::new(BufWriter::new(std::io::stdout()));
            Some(NdjsonWriter::new(bw))
        };

    for mask in AdmissibleParityIter::new(k) {
        let t_compose = Instant::now();
        let pb = ParityBlock::from_mask(mask, k);
        compose_total_ns += t_compose.elapsed().as_nanos();
        let rec = ParityBlockRecord::from(&pb);
        if let Some(ref mut w) = writer {
            let t_write = Instant::now();
            w.write(&rec)?;
            write_total_ns += t_write.elapsed().as_nanos();
        }
        count += 1;
    }

    if let Some(ref mut w) = writer {
        w.flush()?;
    }

    let total = t0.elapsed();
    let secs = total.as_secs_f64();
    eprintln!("[cee_generate] done: {} records in {:.3}s  ({:.2}e6 rec/s)",
              count, secs, count as f64 / secs / 1e6);
    if compose_total_ns > 0 {
        eprintln!("[cee_generate] compose: {:.2}e6/s",
                  count as f64 / (compose_total_ns as f64 / 1e9) / 1e6);
    }
    if write_total_ns > 0 {
        eprintln!("[cee_generate] write  : {:.2}e6/s",
                  count as f64 / (write_total_ns as f64 / 1e9) / 1e6);
    }
    Ok(())
}
