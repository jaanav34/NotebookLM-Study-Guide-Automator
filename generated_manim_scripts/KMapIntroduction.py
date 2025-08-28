from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService


class KMapIntroduction(VoiceoverScene):
    """
    A Manim scene introducing the concept of Karnaugh Maps.

    This scene provides a visual explanation that Karnaugh Maps are a graphical
    method used for simplifying boolean expressions, synchronized with voice narration.
    """

    def construct(self):
        """
        Constructs the animations for the scene.
        """
        # Set the speech service for text-to-speech narration.
        self.set_speech_service(GTTSService())

        # The narration text that will be spoken during the scene.
        narration_text = "Karnaugh Maps provide a graphical method for simplifying boolean expressions."

        # === Mobject Creation ===

        # Title text for "Karnaugh Maps"
        title = Tex("Karnaugh Maps").scale(1.2).to_edge(UP)

        # A 2x2 grid representing the "graphical method" of a K-map.
        kmap_grid = Table(
            [["", ""], ["", ""]],
            h_buff=1.5,
            v_buff=1.5
        ).scale(0.8)

        # Labels for the K-map grid (A, B, 0, 1).
        label_A = MathTex("A").next_to(kmap_grid.get_rows(), LEFT, buff=0.5).shift(UP * 0.75)
        label_0_row = MathTex("0").next_to(kmap_grid.get_rows()[0], LEFT, buff=0.2)
        label_1_row = MathTex("1").next_to(kmap_grid.get_rows()[1], LEFT, buff=0.2)
        row_labels = VGroup(label_A, label_0_row, label_1_row)

        label_B = MathTex("B").next_to(kmap_grid.get_columns(), UP, buff=0.5).shift(LEFT * 0.75)
        label_0_col = MathTex("0").next_to(kmap_grid.get_columns()[0], UP, buff=0.2)
        label_1_col = MathTex("1").next_to(kmap_grid.get_columns()[1], UP, buff=0.2)
        col_labels = VGroup(label_B, label_0_col, label_1_col)

        # Group all K-map elements together for easier manipulation.
        kmap_group = VGroup(kmap_grid, row_labels, col_labels).shift(LEFT * 3.5)

        # Mobjects representing the "simplifying boolean expressions" concept.
        complex_expr = MathTex(r"\overline{A}\overline{B} + \overline{A}B + A\overline{B}")
        arrow = Arrow(LEFT, RIGHT)
        simple_expr = MathTex(r"\overline{A} + \overline{B}")
        
        # Group the expression elements and arrange them.
        expression_group = VGroup(complex_expr, arrow, simple_expr).arrange(RIGHT, buff=0.5).scale(0.8)
        expression_group.next_to(kmap_group, RIGHT, buff=1.0)

        # === Animation Sequence ===

        # Use the voiceover context manager to sync animations with narration.
        with self.voiceover(text=narration_text) as tracker:
            # Animate the title "Karnaugh Maps" as the first words are spoken.
            self.play(
                Write(title),
                run_time=tracker.time_until_word("provide")
            )

            # As the narrator says "graphical method", create the K-map grid.
            self.play(
                Create(kmap_group),
                run_time=tracker.time_between_words("provide", "for")
            )

            # As the narrator mentions "simplifying boolean expressions",
            # show a complex expression being simplified.
            self.play(
                Write(expression_group),
                run_time=tracker.duration - tracker.time_until_word("for")
            )

        # Pause at the end to let the viewer absorb the information.
        self.wait(2)