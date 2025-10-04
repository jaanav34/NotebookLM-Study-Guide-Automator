from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService

class KMapIntroduction(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService())

        # Define the full narration text for the voiceover
        narration_text = (
            "Karnaugh Maps (K-Maps) provide a graphical method for simplifying "
            "Boolean expressions and designing minimal-cost combinational logic circuits. "
            "They are crucial for both Sum-of-Products (SoP) and Product-of-Sums (PoS) minimisation."
        )

        # Create the main text Mobject with proper layout using newlines
        full_text_str_display = (
            "Karnaugh Maps (K-Maps)\n"
            "provide a graphical method for simplifying\n"
            "Boolean expressions and designing minimal-cost\n"
            "combinational logic circuits.\n\n"
            "They are crucial for both Sum-of-Products (SoP)\n"
            "and Product-of-Sums (PoS) minimisation."
        )

        main_text = Text(
            full_text_str_display,
            font_size=36,
            line_spacing=1.2,
            color=WHITE  # Initial color for all text
        )
        main_text.center() # Position the main text in the center of the screen

        # Add the reference text below the main text
        reference = Text("[1d, 1e].", font_size=20, color=GREY)
        reference.next_to(main_text, DOWN, buff=0.7)
        reference.align_to(main_text, LEFT) # Align reference to the left edge of the main text

        # Define colors for highlighting key terms
        HIGHLIGHT_COLOR_1 = YELLOW
        HIGHLIGHT_COLOR_2 = BLUE
        HIGHLIGHT_COLOR_3 = GREEN
        HIGHLIGHT_COLOR_4 = ORANGE
        HIGHLIGHT_COLOR_5 = PINK
        HIGHLIGHT_COLOR_6 = PURPLE

        # Start the voiceover and synchronize animations
        with self.voiceover(text=narration_text) as tracker:
            # Animate the entire main text appearing quickly at the beginning
            self.play(Write(main_text), run_time=2)

            # Wait for a brief moment to allow the narration to catch up with the initial display
            self.wait(0.5)

            # Highlight "Karnaugh Maps (K-Maps)" as it is spoken
            kmap_phrase = main_text.get_part_by_string("Karnaugh Maps (K-Maps)")
            self.play(kmap_phrase.animate.set_color(HIGHLIGHT_COLOR_1), run_time=0.5)
            self.wait(1.0) # Pause to let narration continue before next highlight

            # Highlight "graphical method"
            graphical_method_phrase = main_text.get_part_by_string("graphical method")
            self.play(graphical_method_phrase.animate.set_color(HIGHLIGHT_COLOR_2), run_time=0.0) # Instant color change
            self.wait(0.8) # Pause

            # Highlight "Boolean expressions"
            boolean_expressions_phrase = main_text.get_part_by_string("Boolean expressions")
            self.play(boolean_expressions_phrase.animate.set_color(HIGHLIGHT_COLOR_3), run_time=0.0) # Instant color change
            self.wait(1.0) # Pause

            # Highlight "minimal-cost combinational logic circuits"
            minimal_cost_phrase = main_text.get_part_by_string("minimal-cost")
            combinational_logic_phrase = main_text.get_part_by_string("combinational logic circuits")
            self.play(
                minimal_cost_phrase.animate.set_color(HIGHLIGHT_COLOR_4),
                combinational_logic_phrase.animate.set_color(HIGHLIGHT_COLOR_4),
                run_time=0.0 # Instant color change for both
            )
            self.wait(1.8) # Pause

            # Highlight "Sum-of-Products (SoP)"
            sop_phrase = main_text.get_part_by_string("Sum-of-Products (SoP)")
            self.play(sop_phrase.animate.set_color(HIGHLIGHT_COLOR_5), run_time=0.0) # Instant color change
            self.wait(1.5) # Pause

            # Highlight "Product-of-Sums (PoS)"
            pos_phrase = main_text.get_part_by_string("Product-of-Sums (PoS)")
            self.play(pos_phrase.animate.set_color(HIGHLIGHT_COLOR_6), run_time=0.0) # Instant color change
            self.wait(0.5) # Pause

            # Fade in the reference text towards the end of the narration
            self.play(FadeIn(reference), run_time=0.5)

        # After all animations within the `with` block, ensure the scene waits for the full
        # duration of the voiceover. This handles any remaining audio time.
        self.wait(tracker.duration)

        # Fade out all elements to end the scene cleanly
        self.play(FadeOut(VGroup(main_text, reference)))
        self.wait(0.5)