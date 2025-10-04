from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService

class KMapStructureAndGrayCode(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService())

        # Main Title for the scene
        title = Text("Mapping a Truth Table or Expression to a K-Map", font_size=48, weight=BOLD)
        title.to_edge(UP)

        # Narration for the title
        with self.voiceover(text="") as tracker:
            self.play(Write(title), run_time=2)
        self.wait(0.5)

        # --- Section 1: Purpose of K-Map ---
        purpose_title = Text("Purpose:", font_size=36, weight=BOLD).next_to(title, DOWN, buff=0.8).align_to(title, LEFT)
        purpose_desc = Text(
            "A K-map represents a truth table in a way that allows for easy visual identification of adjacent minterms or maxterms.",
            font_size=30, line_spacing=1.2
        ).next_to(purpose_title, DOWN, buff=0.3).align_to(purpose_title, LEFT)
        
        # Visual metaphor: Truth Table -> K-Map
        truth_table_label = Text("Truth Table", font_size=30, color=BLUE).shift(LEFT * 3 + DOWN * 0.5)
        kmap_concept_label = Text("K-Map", font_size=30, color=GREEN).shift(RIGHT * 3 + DOWN * 0.5)
        arrow_tt_kmap = Arrow(truth_table_label.get_right(), kmap_concept_label.get_left(), buff=0.1, color=WHITE)

        with self.voiceover(text="") as tracker:
            self.play(Write(purpose_title), FadeIn(purpose_desc), run_time=2)
            self.play(
                FadeIn(truth_table_label, shift=LEFT),
                FadeIn(kmap_concept_label, shift=RIGHT),
                GrowArrow(arrow_tt_kmap),
                run_time=2
            )
        self.wait(0.5)

        # Clean up purpose section
        self.play(
            FadeOut(purpose_title),
            FadeOut(purpose_desc),
            FadeOut(truth_table_label),
            FadeOut(kmap_concept_label),
            FadeOut(arrow_tt_kmap),
            run_time=1.5
        )

        # --- Section 2: Structure of K-Map ---
        structure_title = Text("Structure:", font_size=36, weight=BOLD).next_to(title, DOWN, buff=0.8).align_to(title, LEFT)
        structure_desc = Text(
            "K-maps are arranged such that adjacent cells (including cells that 'wrap around' the edges) differ by only one variable.",
            font_size=30, line_spacing=1.2
        ).next_to(structure_title, DOWN, buff=0.3).align_to(structure_title, LEFT)

        with self.voiceover(text="") as tracker:
            self.play(Write(structure_title), FadeIn(structure_desc), run_time=2)
        self.wait(0.5)

        # Create a 2x4 K-map for a 3-variable system (A, B, C)
        # Cells represent minterms using their indices (m0-m7)
        m0 = Tex("$m_0$", font_size=30, color=WHITE) # 000
        m1 = Tex("$m_1$", font_size=30, color=WHITE) # 001
        m3 = Tex("$m_3$", font_size=30, color=WHITE) # 011
        m2 = Tex("$m_2$", font_size=30, color=WHITE) # 010
        m4 = Tex("$m_4$", font_size=30, color=WHITE) # 100
        m5 = Tex("$m_5$", font_size=30, color=WHITE) # 101
        m7 = Tex("$m_7$", font_size=30, color=WHITE) # 111
        m6 = Tex("$m_6$", font_size=30, color=WHITE) # 110

        kmap_matrix = [
            [m0, m1, m3, m2],
            [m4, m5, m7, m6]
        ]
        
        # Column and Row labels for the K-map
        col_labels = VGroup(Tex("00"), Tex("01"), Tex("11"), Tex("10"))
        row_labels = VGroup(Tex("0"), Tex("1"))
        
        kmap_table = MobjectTable(
            kmap_matrix,
            col_labels=col_labels,
            row_labels=row_labels,
            include_outer_lines=True,
            line_config={"stroke_width": 2, "color": LIGHT_GRAY},
            h_buff=1.0, # Horizontal buffer between cells
            v_buff=0.6  # Vertical buffer between cells
        )
        kmap_table.scale(0.8).center().shift(DOWN * 0.5)

        # Add overall A and BC labels for the axes
        label_A = Tex("A", font_size=36, color=YELLOW).next_to(kmap_table.get_rows()[0], LEFT, buff=0.5).shift(UP * 0.3)
        label_BC = Tex("BC", font_size=36, color=YELLOW).next_to(kmap_table.get_columns()[0], UP, buff=0.5).shift(LEFT * 0.3)
        
        kmap_group = VGroup(kmap_table, label_A, label_BC)

        with self.voiceover(text="") as tracker:
            self.play(FadeIn(kmap_group, shift=UP), run_time=2)
        self.wait(0.5)

        # Explanation about Boolean identity
        boolean_identity_text = Text(
            "This adjacency represents the Boolean algebra identity X + X' = 1 or (X)(X') = 0, which is key to simplification.",
            font_size=30, line_spacing=1.2
        ).next_to(kmap_table, DOWN, buff=0.8).align_to(kmap_table, LEFT)
        
        boolean_identity_math = MathTex("X + X' = 1", font_size=40, color=RED).next_to(boolean_identity_text, DOWN, buff=0.3).align_to(boolean_identity_text, LEFT)

        # Helper function to get a surrounding rectangle for a K-map cell
        def get_cell_highlight(table, row_idx, col_idx, color=YELLOW):
            return SurroundingRectangle(table.get_rows()[row_idx][col_idx], color=color, stroke_width=4, buff=0.05)

        with self.voiceover(text="") as tracker:
            # Highlight a horizontal adjacency (m0-m1)
            rect_h_1 = get_cell_highlight(kmap_table, 0, 0, color=ORANGE)
            rect_h_2 = get_cell_highlight(kmap_table, 0, 1, color=ORANGE)
            self.play(Create(rect_h_1), Create(rect_h_2), run_time=1.5)
            self.wait(0.5)

            # Highlight a vertical adjacency (m0-m4)
            rect_v_1 = get_cell_highlight(kmap_table, 0, 0, color=GREEN)
            rect_v_2 = get_cell_highlight(kmap_table, 1, 0, color=GREEN)
            self.play(Transform(rect_h_1, rect_v_1), Transform(rect_h_2, rect_v_2), run_time=1.5) # Reuse mobjects
            self.wait(0.5)

            # Highlight a wrap-around adjacency (m0-m2)
            rect_w_1 = get_cell_highlight(kmap_table, 0, 0, color=PURPLE)
            rect_w_2 = get_cell_highlight(kmap_table, 0, 3, color=PURPLE)
            self.play(Transform(rect_h_1, rect_w_1), Transform(rect_h_2, rect_w_2), run_time=1.5) # Reuse mobjects
            self.wait(0.5)
            self.play(FadeOut(rect_h_1, rect_h_2), run_time=0.5) # Fade out the highlight

            self.play(FadeIn(boolean_identity_text, shift=UP), run_time=1.5)
            self.play(Write(boolean_identity_math), run_time=1.5)
        self.wait(0.5)

        # Clean up structure section visuals
        self.play(
            FadeOut(structure_title),
            FadeOut(structure_desc),
            FadeOut(boolean_identity_text),
            FadeOut(boolean_identity_math),
            run_time=1.5
        )

        # --- Section 3: Variable Order (Gray Code) ---
        variable_order_title = Text("Variable Order:", font_size=36, weight=BOLD).next_to(title, DOWN, buff=0.8).align_to(title, LEFT)
        gray_code_desc = Text(
            "Variables on the map's axes follow a Gray code sequence (e.g., 00, 01, 11, 10) to ensure single-bit changes between adjacent cells.",
            font_size=30, line_spacing=1.2
        ).next_to(variable_order_title, DOWN, buff=0.3).align_to(variable_order_title, LEFT)
        
        # Shift K-map up slightly to make room for Gray code explanation
        self.play(
            kmap_group.animate.shift(UP * 0.5), 
            Write(variable_order_title),
            FadeIn(gray_code_desc),
            run_time=2
        )
        self.wait(0.5)
        
        # Get the column labels from the K-map table for highlighting
        col_labels_on_map = kmap_table.col_labels 
        gray_codes_sequence_str = ["00", "01", "11", "10"] # String representation for comparison

        # Create a VGroup of Tex objects to display the Gray code sequence explicitly
        display_gray_codes = VGroup()
        for i, code_str in enumerate(gray_codes_sequence_str):
            code_mobj = Tex(code_str, font_size=40, color=BLUE)
            if i == 0:
                code_mobj.next_to(gray_code_desc, DOWN, buff=0.8)
            else:
                code_mobj.next_to(display_gray_codes[-1], RIGHT, buff=0.8)
            display_gray_codes.add(code_mobj)
        display_gray_codes.center().shift(DOWN * 1.5)

        # Show the first Gray code and indicate its corresponding column on the K-map
        with self.voiceover(text="") as tracker:
            self.play(FadeIn(display_gray_codes[0]), run_time=1)
            self.play(Indicate(col_labels_on_map[0], scale_factor=1.3, color=YELLOW), run_time=1)
        self.wait(0.5)

        # Animate the sequence and highlight single-bit changes
        arrow_between_codes = Arrow(ORIGIN, ORIGIN, color=WHITE, buff=0.2, max_tip_length_to_length_ratio=0.25)
        
        for i in range(len(gray_codes_sequence_str) - 1):
            current_code_mobj = display_gray_codes[i]
            next_code_mobj = display_gray_codes[i+1]
            
            # Position the arrow between the current and next code
            arrow_between_codes.put_start_and_end_on(current_code_mobj.get_right(), next_code_mobj.get_left())
            
            # Get the string values for bit-by-bit comparison
            current_code_str = gray_codes_sequence_str[i]
            next_code_str = gray_codes_sequence_str[i+1]

            # Create temporary highlights for the bits that change
            bit_highlights = VGroup()
            for char_idx in range(len(current_code_str)):
                if current_code_str[char_idx] != next_code_str[char_idx]:
                    # Create a circle to highlight the changing bit in the displayed sequence
                    circle_current = Circle(radius=0.15, color=RED, stroke_width=4).move_to(current_code_mobj[char_idx])
                    circle_next = Circle(radius=0.15, color=RED, stroke_width=4).move_to(next_code_mobj[char_idx])
                    bit_highlights.add(circle_current, circle_next)

            with self.voiceover(text="") as tracker:
                # Show the next Gray code, the arrow, and indicate its column on the K-map
                self.play(
                    GrowArrow(arrow_between_codes),
                    FadeIn(next_code_mobj),
                    Indicate(col_labels_on_map[i+1], scale_factor=1.3, color=YELLOW),
                    run_time=1.5
                )
                # Animate the bit change highlight
                if len(bit_highlights) > 0:
                    self.play(Create(bit_highlights), run_time=1)
            self.wait(0.3)
            # Fade out highlights before the next iteration
            self.play(FadeOut(bit_highlights), run_time=0.5)

        # Clean up Gray code section visuals
        with self.voiceover(text="") as tracker:
            self.play(
                FadeOut(display_gray_codes), 
                FadeOut(arrow_between_codes), 
                FadeOut(variable_order_title),
                FadeOut(gray_code_desc),
                FadeOut(kmap_group), # Fade out the entire K-map and its labels
                FadeOut(title), # Fade out the main title
                run_time=2
            )
        self.wait(1)