1. SoP, PoS, K-Maps, and Timing Hazards (30%)
(a) Sum of Products (SoP) and Product of Sums (PoS) Representations
Define SoP (minterm-based) and PoS (maxterm-based) representations
Explain Canonical Sum (Sum of Minterms) and Canonical Product (Product of Maxterms)
Demonstrate how to convert between shorthand notation (ON set/OFF set) and full expressions
Sources: lec2.1SoPPoSKMaps1.pdf, Supplement 2A Combinational Circuit Analysis and Synthesis.pdf
(b) Karnaugh Maps (K-Maps)
Explain how to map a truth table, SoP/PoS expression, Canonical Sum, or Canonical Product onto a K-map
Provide step-by-step minimization of logic expressions using K-maps for up to 4 variables
Address handling of don’t care conditions
Sources: lec2.1SoPPoSKMaps1.pdf, Supplement 2A Combinational Circuit Analysis and Synthesis.pdf
(c) Timing Hazards in Combinational Circuits
Define static-1, static-0, dynamic 1-to-0, and dynamic 0-to-1 hazards
Illustrate how to identify hazards in circuit designs using K-maps
Describe design techniques for hazard-free circuits
Sources: lec2.2Harzards.pdf, Supplement 2B Timing Hazards.pdf

2. Decoders (15%)
(a) Understanding Decoders
Define n:2ⁿ decoders and explain their role in digital circuits
Compare high-active (minterm-based) vs. low-active (maxterm-based) outputs
Explain the use of enable signals
Sources: lec2.5Decoders1.pdf, Supplement 2D Decoders and Demultiplexers.pdf
(b) Designing Decoders
Demonstrate logic gate-based implementation of a decoder
Illustrate how to expand decoders using decoder trees
Sources: lec2.5Decoders1.pdf, Supplement 2D Decoders and Demultiplexers.pdf
(c) Using Decoders for Logic Function Implementation
Explain how decoders can be used to implement arbitrary Boolean functions
Provide step-by-step examples of using decoders in circuit design
Sources: lec2.5Decoders1.pdf, Supplement 2D Decoders and Demultiplexers.pdf

3. Encoders and More (15%)
(a) Understanding Encoders
Define 2ⁿ:n binary-to-decimal encoders, priority encoders, and decoders with strobe output
Discuss differences between basic encoders and priority encoders
Sources: lec2.6Encoders.pdf, Supplement 2E Encoders.pdf
(b) Designing Encoders
Explain how to implement an encoder using basic logic gates
Illustrate encoder truth tables and Boolean expressions
Sources: lec2.6Encoders.pdf, Supplement 2E Encoders.pdf
(c) Additional Concepts
Discuss Programmable Logic Devices (PLDs), Read-Only Memory (ROM), Look-Up Tables (LUTs), and Field-Programmable Gate Arrays (FPGAs)
Explain Open-Drain Outputs, Tri-State Buffers, and Transmission Gates
Sources: lec2.4ROM_LUT.pdf, Supplement 2C Programmable Logic Devices.pdf

4. Multiplexers (15%)
(a) Understanding Multiplexers
Define 2ⁿ:1 multiplexers and explain their function as multiway switches controlled by select lines
Illustrate truth tables and logic expressions for multiplexers
Sources: lec2.3Mux.pdf, Supplement 2F Multiplexers.pdf
(b) Designing Multiplexers
Demonstrate how to design a multiplexer using basic logic gates
Explain how to cascade multiple multiplexers to build larger multiplexer systems
Sources: lec2.3Mux.pdf, Supplement 2F Multiplexers.pdf
(c) Using Multiplexers to Implement Logic Functions
Show how to implement arbitrary logic functions using multiplexers
Provide an example of constructing a MUX-tree
Sources: lec2.3Mux.pdf, Supplement 2F Multiplexers.pdf

5. Verilog Designs (25%)
(a) Verilog Modeling Approaches
Define and differentiate:
Structural modeling using primitive gates
Dataflow modeling using continuous assignments
Behavioral modeling using procedural blocks
(b) Hierarchical Verilog Design & Module Instantiation
Explain module instantiation using connection by name vs. connection by order
Demonstrate how to structure Verilog designs with multiple submodules
(c) Verilog Implementations of Common Digital Blocks
Provide Verilog implementations for:
Decoders
Encoders
Multiplexers
Binary-Coded Decimal (BCD) to 7-Segment Code Converters

