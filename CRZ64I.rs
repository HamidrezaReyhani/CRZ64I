use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::thread;
use regex::Regex;  // For better parsing (add dependency if needed, but assume available)

#[derive(Clone)]
struct CRZ64I_Emulator {
    regs: [u64; 32],
    vregs: Vec<[u64; 2]>,
    memory: Arc<Mutex<Vec<u8>>>,
    pc: usize,
    flags: HashMap<String, u8>,
    halted: bool,
    labels: HashMap<String, usize>,  // For branches
    log: Vec<String>,  // For determinism replay
}

impl CRZ64I_Emulator {
    fn new() -> Self {
        let mut flags = HashMap::new();
        flags.insert("Z".to_string(), 0);
        flags.insert("N".to_string(), 0);
        flags.insert("C".to_string(), 0);
        flags.insert("V".to_string(), 0);

        CRZ64I_Emulator {
            regs: [0; 32],
            vregs: vec![[0, 0]; 8],
            memory: Arc::new(Mutex::new(vec![0; 4096])),
            pc: 0,
            flags,
            halted: false,
            labels: HashMap::new(),
            log: Vec::new(),
        }
    }

    fn parse_reg(&self, s: &str) -> usize {
        s.trim_matches(|c: char| c == 'r' || c == ',' || c.is_whitespace()).parse().unwrap_or(0)
    }

    fn execute(&mut self, instr: &str) {
        self.log.push(instr.to_string());  // Log for replay
        let re = Regex::new(r"(\w+)\s*(r\d+)?\s*,?\s*(r\d+|\#\d+)?\s*,?\s*(r\d+|\#\d+|\[.*\])?").unwrap();
        if let Some(caps) = re.captures(instr) {
            let opcode = caps.get(1).map_or("", |m| m.as_str()).to_uppercase();

            match opcode.as_str() {
                "MOVI" => {
                    let rd = self.parse_reg(caps.get(2).map_or("", |m| m.as_str()));
                    let imm: u64 = caps.get(3).map_or(0, |m| m.as_str().trim_start_matches('#').parse().unwrap());
                    self.regs[rd] = imm;
                }
                "LOAD" => {
                    let rd = self.parse_reg(caps.get(2).map_or("", |m| m.as_str()));
                    let addr_str = caps.get(4).map_or("", |m| m.as_str()).trim_matches(|c| c == '[' || c == ']');
                    let base = self.parse_reg(addr_str.split('+').next().unwrap_or(""));
                    let off: usize = addr_str.split('+').nth(1).map_or(0, |s| s.parse().unwrap());
                    let addr = self.regs[base] as usize + off;
                    let mut mem = self.memory.lock().unwrap();
                    if addr + 8 > mem.len() { panic!("Out of bounds"); }
                    let value = u64::from_le_bytes(mem[addr..addr+8].try_into().unwrap());
                    self.regs[rd] = value;
                }
                "ADD" => {
                    let rd = self.parse_reg(caps.get(2).map_or("", |m| m.as_str()));
                    let rs1 = self.parse_reg(caps.get(3).map_or("", |m| m.as_str()));
                    let op2_str = caps.get(4).map_or("", |m| m.as_str());
                    let op2 = if op2_str.starts_with('#') { op2_str[1..].parse::<u64>().unwrap() } else { self.regs[self.parse_reg(op2_str)] };
                    let a = self.regs[rs1];
                    let (sum, carry) = a.overflowing_add(op2);
                    let v = ((a ^ sum) & (op2 ^ sum) & (1u64 << 63)) != 0;  // Signed overflow
                    self.regs[rd] = sum;
                    self.flags.insert("Z".to_string(), if sum == 0 {1} else {0});
                    self.flags.insert("N".to_string(), if (sum & (1u64 << 63)) != 0 {1} else {0});
                    self.flags.insert("C".to_string(), if carry {1} else {0});
                    self.flags.insert("V".to_string(), if v {1} else {0});
                }
                "BNE" => {
                    let label = caps.get(2).map_or("", |m| m.as_str());
                    if self.flags["Z"] == 0 {
                        self.pc = *self.labels.get(label).unwrap_or(&0) - 1;  // Adjust for pc+=1
                    }
                }
                // Add XCHG, INC, etc. similarly...
                _ => {}
            }
        }
    }

    fn run_program(&mut self, program: Vec<String>) {
        // Build labels first
        for (i, instr) in program.iter().enumerate() {
            if instr.ends_with(':') {
                self.labels.insert(instr.trim_end_matches(':').to_string(), i);
            }
        }
        while self.pc < program.len() && !self.halted {
            self.execute(&program[self.pc]);
            self.pc += 1;
        }
    }
}

fn main() {
    let mut emulator = CRZ64I_Emulator::new();
    // Set memory...
    // Program with loop label
    let program = vec![
        "MOVI r1 #256".to_string(),
        "MOVI r2 #4".to_string(),
        "MOVI r3 #0".to_string(),
        "loop:".to_string(),
        "LOAD r4 [r1]".to_string(),
        "ADD r3 r3 r4".to_string(),
        "ADD r1 r1 #8".to_string(),
        "DEC r2".to_string(),
        "BNE loop".to_string(),  // Now works
    ];
    emulator.run_program(program);
    println!("Sum: {}", emulator.regs[3]);
}