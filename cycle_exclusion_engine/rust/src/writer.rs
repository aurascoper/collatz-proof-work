//! NDJSON and binary writers.

use std::io::{BufWriter, Write};
use std::fs::File;
use std::path::Path;

use crate::record::ParityBlockRecord;

pub struct NdjsonWriter<W: Write> {
    inner: W,
    count: u64,
}

impl NdjsonWriter<BufWriter<File>> {
    pub fn create<P: AsRef<Path>>(path: P) -> std::io::Result<Self> {
        let f = File::create(path)?;
        Ok(Self { inner: BufWriter::with_capacity(1 << 20, f), count: 0 })
    }
}

impl<W: Write> NdjsonWriter<W> {
    pub fn new(w: W) -> Self {
        Self { inner: w, count: 0 }
    }
    pub fn write(&mut self, rec: &ParityBlockRecord) -> std::io::Result<()> {
        serde_json::to_writer(&mut self.inner, rec)?;
        self.inner.write_all(b"\n")?;
        self.count += 1;
        Ok(())
    }
    pub fn count(&self) -> u64 {
        self.count
    }
    pub fn flush(&mut self) -> std::io::Result<()> {
        self.inner.flush()
    }
}

/// Stub for the binary path. Filled in if/when NDJSON throughput is
/// insufficient.
pub struct BinaryWriter;
