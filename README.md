# CRZ64I — مشخصات رسمی (مستند جامع)

## 1. خلاصه و هدف

CRZ64I یک ISA و زبانِ سطح میانی/زبان برنامه‌نویسی سیستمی است که برای چهار هدف طراحی شده:

1. کاهش تعداد سیکل‌های اجرای هر دستور از طریق فشرده‌سازی و Fusion.
2. اجرای نهایی با کمترین latency ممکن و پشتیبانی از الگوهای real-time.
3. کاهش مصرف انرژی در پردازش، آماده‌سازی، ذخیره و انتقال داده.
4. مینیمایز کردن تولید حرارت از طریق نرم‌افزار-محور و الگوهای reversible/energy-aware.

طراحی CRZ64I طوری است که با معماری‌های سخت‌افزاری موجود (x86, ARM, RISC-V و انواع coreها) سازگار باشد و نیازی به سخت‌افزار خاص برای استفادهٔ پایه‌ای نداشته باشد. افزونه‌ها (extensions) برای بهره‌برداری از سخت‌افزار خاص نیز تعریف شده‌اند.

---

## 2. فهرست مطالب (این مستند)

1. خلاصه و هدف
2. گرامر پایه و صفت‌ها (attributes)
3. انواع داده و مدل حافظه
4. رجیسترها و فضای اجرای پایه
5. مجموعهٔ ۶۴ دستور (طبقه‌بندی + شرح کوتاه هر دستور)
6. کدگذاری و قالب دستور (نمونهٔ باینری/متن)
7. صفات/هینت‌ها و semantics (fusion, reversible, no_erase, power, realtime, thermal_hint و ZDRT/IZSO)
8. کامپایلر: passes و تبدیل‌ها (fusion pass, reversible-emulation, energy-aware RA)
9. Runtime / Scheduler / ABI / Calling convention
10. الگوهای برنامه‌نویسی و کتابخانهٔ استاندارد (math, vector, io, sync)
11. ابزارها: assembler, disassembler, simulator, harness برای bench
12. تست، متریک‌ها و روش بنچمارک
13. امنیت، sandboxing و محدودیت‌ها
14. توسعه، مشارکت و Licensing (OpenLogic)
15. پیوست: نمونه‌ها، تست‌های کوچک، چک‌لیست تحویل

---

## 3. گرامر پایه و صفت‌ها (مختصر)

گرامر ساده (EBNF خلاصه):

```
program ::= { top_decl } ;
top_decl ::= attribute_list? ( function_decl | global_inst ) ;
attribute_list ::= { attribute } ;
attribute ::= "#[" identifier [ "=" value ] "]" ;
function_decl ::= "fn" identifier "(" param_list? ")" block ;
block ::= "{" { statement } "}" ;
statement ::= attribute_list? ( instruction ";" | local_decl | return_stmt | label ) ;
instruction ::= mnemonic operand_list? ;
operand ::= identifier | number | "[" memory_ref "]" ;
```

صفت‌های اصلی و semantics کوتاه:

* `#[fusion]` — اجازهٔ Fuse کردن دستورات مجاور. (Hint)
* `#[reversible]` — تابع/بلوک باید بدون information-erasure اجرا شود یا دلتاها ذخیره شوند.
* `#[no_erase]` — دستور/اعلان از پاک‌سازی اطلاعات قبلی بپرهیزد.
* `#[power="low"|"med"|"high"|<int>]` — hint برای ترجمه به low-power mode.
* `#[realtime]` — تضمین رفتار Deterministic/WCET-friendly.
* `#[thermal_hint=<0..N>]` — hint برای scheduler جهت کم‌کردن داغ شدن.

---

## 4. انواع داده، مدل حافظه، رجیسترها

* انواع داده پایه: `i8,i16,i32,i64, u8..u64, f32, f64, vec<n,type>` و `ptr`.
* مدل حافظه: **SC (sequential consistency) by default** برای semantic ساده. در سطح بهینه‌سازی کامپایلر می‌توان relaxed modes برای performance فعال کرد ولی `#[realtime]` توابع باید deterministic رفتار دهند.
* حافظه مجازی وابسته به پلتفرم میزبان. CRZ64I فرض می‌کند صفحات 4KB، alignment طبیعی، و دسترسی‌های atomic را پشتیبانی می‌کنیم.
* رجیسترها (سطح ISA منطقی):

  * 32 رجیستر عمومی `R0..R31` (i64 width) — تقسیم شده به رجیسترهای محلی و آرگومان‌ها.
  * 16 رجیستر برداری `V0..V15` (128/256/512-bit logical lane).
  * PC, SP, FP, FLAGS.
  * امکان map به رجیسترهای فیزیکی میزبان توسط backend.

---

## 5. مجموعهٔ ۶۴ دستور — طبقه‌بندی و شرح

(اینجا ۶۴ دستور در 10 گروه تعریف شده؛ نام‌ها و semantics عملیاتی ارائه شده تا مستند کامل شود.)

### 5.1 گروه کنترل (8 دستور)

1. `NOP` — بدون عمل.
2. `BR label` — jump مطلق.
3. `BR_IF cond, label` — conditional jump.
4. `CALL label` — call (stack push return).
5. `RET` — return.
6. `YIELD` — cooperative yield (runtime hint).
7. `TRAP code` — باگ/exception با کد.
8. `HALT` — توقف.

### 5.2 محاسبات صحیح و بیتی (10 دستور)

9. `ADD rd, rs1, rs2`
10. `SUB rd, rs1, rs2`
11. `MUL rd, rs1, rs2`
12. `DIV rd, rs1, rs2`
13. `AND rd, rs1, rs2`
14. `OR rd, rs1, rs2`
15. `XOR rd, rs1, rs2`
16. `SHL rd, rs1, imm`
17. `SHR rd, rs1, imm`
18. `POPCNT rd, rs1`

### 5.3 حافظه و I/O پایه (8 دستور)

19. `LOAD rd, [addr]` — بارگذاری.
20. `STORE rs, [addr]` — نوشتن.
21. `LOADF rd, [addr]` — بار float.
22. `ATOMIC_INC [addr]` — atomic increment.
23. `DMA_START src, dst, len` — hint برای DMA/BLIT.
24. `CACHE_LOCK addr, size` — hint نگهداری در cache.
25. `PREFETCH addr`
26. `MMAP rd, addr, size` — map memory.

### 5.4 عملیات برداری و SIMD (10 دستور)

27. `VLOAD vx, [addr]`
28. `VSTORE vx, [addr]`
29. `VADD vx, vy, vz`
30. `VSUB vx, vy, vz`
31. `VMUL vx, vy, vz`
32. `VDOT32 vd, va, vb` — dot 32-bit lanes.
33. `VSHL vx, imm`
34. `VSHR vx, imm`
35. `VFMA vd, va, vb, vc` — vector fused multiply-add.
36. `VREDUCE_SUM rd, vx`

### 5.5 محاسبات نقطه‌ای (4 دستور)

37. `FADD fd, fa, fb`
38. `FSUB fd, fa, fb`
39. `FMUL fd, fa, fb`
40. `FMA fd, fa, fb, fc`

### 5.6 عملیات اتمیک/همگام‌سازی (4 دستور)

41. `LOCK addr`
42. `UNLOCK addr`
43. `CMPXCHG [addr], expected, new`
44. `FENCE` — memory barrier

### 5.7 سیستم و مدیریت انرژی/ترمال (6 دستور)

45. `SET_PWR_MODE mode` — change DVFS hint.
46. `GET_PWR_STATE rd`
47. `THERM_READ rd` — read thermal sensor (hint).
48. `SET_THERM_POLICY policy`
49. `SLEEP ms` — low-power wait.
50. `FAST_PATH_ENTER` — hint to runtime to enable low-latency optimized path.

### 5.8 reversible / zero-dissipation helpers (6 دستور)

51. `SAVE_DELTA tmp, target` — save delta for reversibility.
52. `RESTORE_DELTA tmp, target`
53. `REV_ADD rd, ra, rb` — reversible form (logical).
54. `REV_SWAP a, b`
55. `ADIABATIC_START` — start low-dissipation mode (hint).
56. `ADIABATIC_STOP`

### 5.9 crypt / hash / checksum (4 دستور)

57. `CRC32 rd, rs, len`
58. `HASH_INIT ctx`
59. `HASH_UPDATE ctx, addr, len`
60. `HASH_FINAL ctx, rd`

### 5.10 امتدادهای محیطی و کمکی (4 دستور)

61. `PROFILE_START id`
62. `PROFILE_STOP id`
63. `TRACE point`
64. `EXTENSION opcode, args` — generic extension hook

> هر دستور دارای semantics روشن، latency و انرژی برآوردی پایه در سند مرجع پیوست است. برای پیاده‌سازی، backend باید نقشهٔ هر mnemonic به micro-op/sequence ایمپلمنت را تعریف کند.

---

## 6. قالب کد متنی و باینری (نمونه)

متن نمونه (assembly-like):

```crz
#[fusion]
fn hot_loop(a, b, n) {
  i = 0;
_loop:
  LOAD r1, [a + i*8];
  VDOT32 v0, r1, b;
  FMA v1, v0, c, v2;
  STORE v1, [a + i*8];
  ADD i, i, 1;
  BR_IF LT i, n, _loop;
}
```

نمونهٔ کد باینری: هر دستور 32 بیت (نمونه) با فیلدهای opcode(8), rd(5), rs1(5), rs2/imm(14). (فرمت باینری دقیق در Annex A)

---

## 7. صفات و semantics تفصیلی

* `#[fusion]`

  * Hint برای compiler/fetch: مجاز به ترکیب متوالی دستورات است اگر semantic حفظ شود. توصیه: کامپایلر یک pass به نام `fusion-pass` پیاده کند.
* `#[reversible]`

  * تابع باید از erasure جلوگیری کند یا دلتاها را ذخیره کند. قوانین: هر write به target که قبلاً state داشته باید یا `#[no_erase]` داشته باشد یا پیش از آن `let tmp = target` (یا `SAVE_DELTA`) اجرا شود. کامپایلر باید dataflow analysis انجام دهد.
* `#[no_erase]`

  * قرار دادن روی دستور به معنی این است که write نباید باعث پاک شدن state فیزیکی شود (در سطح اجرا runtime/allocator می‌تواند copy-on-write یا append انجام دهد).
* `#[power="low"]`

  * hint برای تبدیل به codegen کم-انرژی: کاهش instruction throughput، افزایش batching، استفاده از DVFS.
* `#[realtime]`

  * الزامات: deterministic memory allocation, no blocking syscalls, WCET annotations. کامپایلر باید بررسی کند.
* `#[thermal_hint=n]`

  * scheduler از این برای تبدیل کاری به هستهٔ خنک‌تر یا مهاجرت به‌کار می‌برد.

### Extensions ویژه (ایده‌های تحقیقی)

* **Fusion Mode**: Macro-op fusion برای جفت‌هایی مانند `LOAD+ADD` یا `LD+VDOT` که micro-op را کاهش می‌دهد.
* **IZSO (Instant-Zero SoftOpt Extension)**: مجموعهٔ بهینه‌سازی نرم‌افزاری برای نزدیک‌شدن به zero-energy بدون تغییر سخت‌افزار (reversible-emulation در compiler، async non-blocking patterns، energy-aware register allocation).
* **ZDRT (Zero-Dissipation Real-Time Extension)**: پروفایل برای ترکیب reversible + photonic/quantum mapping اگر سخت‌افزار پشتیبانی کند. در حالت فعلی بیشتر به عنوان hint و الگوریتم تبدیل مطرح است.

---

## 8. کامپایلر و passes پیشنهادی

1. **Front-end** — parse, AST, attribute attach.
2. **Semantic check pass** — validate attributes (e.g., `#[realtime]` constraints).
3. **Fusion pass** — detect patterns and rewrite to fused-instructions or intrinsics.
4. **Reversible-emulation pass** — insert `SAVE_DELTA`/`RESTORE_DELTA` یا transform algs به شکل reversible.
5. **Energy-aware RA & scheduling** — cost model Joules/op و تخصیص رجیستر انرژی-محور.
6. **Lowering** — map logical ISA به target micro-ops.
7. **Backend** — register allocation, instruction selection, codegen برای x86/ARM/RISCV.
8. **Linker/Optimizer** — profile-guided optimization (PGO) و power/thermal profile feedback.

---

## 9. Runtime، Scheduler، ABI

* **ABI**: آرگومان‌ها در R0..R5، باقی در استک. Caller-saved و callee-saved طبق convention تعیین شود. Stack-alignment 16 bytes.
* **Runtime**:

  * Thread model: lightweight threads (user-level) و kernel threads.
  * Scheduler supports thermal-aware policies, power modes, and `FAST_PATH_ENTER` hints.
  * IPC: zero-copy message passing، lock-free queues، and `DMA_START` hints for bulk moves.
* **Garbage & Memory**:

  * برای reversible modes پیشنهاد: arena allocators و explicit `free` به منظور جلوگیری از implicit erasure.
* **Profiling**:

  * `PROFILE_START/STOP` برای fine-grained performance and energy measurement.

---

## 10. کتابخانهٔ استاندارد و الگوها

* `crz::math` — BLAS-like kernels (GEMM optimized), FFT, VDOT helpers.
* `crz::mem` — lowpower::alloc, cache pinning, zero-copy IO.
* `crz::sync` — lock-free queues, epoch-based reclamation (for reversible emulation use special reclamation).
* `crz::io` — DMA wrappers, async IO, low-latency networking primitives.
* الگوریتم‌ها: reversible-sort, reversible-scan, block-tiling GEMM, fused micro-kernels.

---

## 11. ابزارها و harness

* **Assembler / Disassembler**: `crz-as`, `crz-objdump`.
* **Simulator**: cycle-accurate simulator with energy and thermal model and toggles for reversible/emulated modes.
* **Microbench harness**: RAPL + perf + sensors integration (مثلاً اسکریپت‌هایی که برای baseline در فاز ۱ ساختیم).
* **Verification tools**: static analyzer for `#[reversible]` (dataflow + path-sensitive CFG analysis). (نمونهٔ PoC را قبلاً فراهم کردم.)

---

## 12. تست، بنچمارک و متریک‌ها

متریک‌های ضروری:

* CPI و cycles/op برای هر دستور بحرانی.
* Joules/op (RAPL یا مدل سیمولیشن).
* P95/P99 latency برای توابع `#[realtime]`.
* دمای پایدار و hotspot maps.

پروتکل بنچمارک:

1. تعریف workloads: microbench (ADD/LOAD/STORE), vector kernels (VDOT32, FMA), end-to-end workloads (GEMM, ML inference).
2. Baseline capture (بدون بهینه‌سازی).
3. اجرای Fusion + Izso + Reversible passes و ثبت تغییرات.
4. گزارش تغییرات energy, cycles, latency, temp.

---

## 13. امنیت و محدودیت‌ها

* محدود کردن `EXTENSION` و `DMA_START` به مجوزهای کاربری.
* Sandbox برای اجرای کدهای ناشناس.
* تجزیه و تحلیل side-channel: reversible modes می‌توانند الگوهای مصرف را تغییر دهند؛ مراقب اطلاعات-افشا (power analysis) باشید.

---

## 14. توسعه، مشارکت و License

* پروژه تحت هستهٔ **OpenLogic** توسعه می‌یابد.
* پیشنهاد لایسنس: OpenLogic permissive license (مشابه MIT/Apache، جزئیات را در repo OpenLogic قرار دهید).
* Contribution flow:

  1. Fork repo → feature branch → PR با bench evidence → security review → merge.
  2. هر extension بزرگ باید RFC مستند داشته باشد (design, microarch impact, energy model).
* لینک مرجع گیت‌هاب (از درخواست شما): `https://github.com/openlogicorg/openlogic` — تمام commits و issues و RFC‌ها آنجا قرار می‌گیرند.

---

## 15. پیوست — مثال‌ها و چک‌لیست تحویل

### مثال: Hello world (I/O فرضی)

```crz
fn main() {
  #[power="low"]
  let msg = "Hello CRZ64I\n";
  DMA_START msg, IO_BUFFER, len(msg);
  EXTENSION WRITE_IO, IO_BUFFER;
  HALT;
}
```

### چک‌لیست فنی برای انتشار نسخهٔ 0.1

* [ ] Grammar رسمی و ANTLR/PEG پیاده‌سازی شده.
* [ ] Parser + semantic checker برای attributes.
* [ ] ۶۴ دستور با encoding اولیه و جدول latency/energy.
* [ ] Fusion pass در LLVM-like IR یا custom backend.
* [ ] Reversible-emulation pass و PoC روی توابع نمونه.
* [ ] Microbench harness و baseline runs.
* [ ] مستند License و contribution flow در GitHub.
* [ ] مجموعهٔ تست‌ها و گزارش بنچمارک اولیه.

---

## 16. گام‌های بعدی پیشنهادی (عملی)

1. اجرا و به‌دست آوردن baseline برای ۶ دستور بحرانی (ADD, LOAD, STORE, VDOT32, FMA, BRANCH).
2. پیاده‌سازی `fusion-pass` ساده برای الگوهای رایج.
3. تکمیل جدول latency/energy به‌صورت تجربی با harness.
4. توسعهٔ reversible pass و اجرای تحلیل داده‌جریان و CFG path-sensitive.
5. انتشار نسخهٔ 0.1 در repo OpenLogic با مستندات، ابزارها و نمونه‌ها.

---

## 17. مواردِ علمی و محدودیت‌ها

* حذف کامل حرارت یا رسیدن به “zero” به‌صورت مطلق با تکنیک‌های نرم‌افزاری ممکن نیست (قوانین ترمودینامیک و Landauer). هدف CRZ64I: نزدیک شدن به حداقل‌های عملیاتی با ترکیب نرم‌افزار و سخت‌افزار موجود.
* تکنیک‌های photonic/quantum/reversible می‌توانند الهام‌بخش باشند و بعضی روش‌ها را می‌توان به‌صورت نرم‌افزاری شبیه‌سازی یا تقریبی پیاده‌سازی کرد؛ اما برای full hardware speed-up نیاز به سخت‌افزار مناسب است.

---

### پایان

این مستند نسخهٔ کامل و عملیاتی پایه برای CRZ64I است. اگر بخواهی:

* آن را به فایل Markdown یا PDF تبدیل کنم،
* جدول کامل ۶۴ دستور با فیلدهای latency/energy و نمونهٔ باینری را برای هر دستور تولید کنم،
* یا بخش خاصی را (مثلاً `reversible-emulation pass` یا `fusion-pass`) با کد نمونه و تست بنچمارک توسعه بدهم،

همین حالا بدون سؤال بگو تا تحویل دهم.
