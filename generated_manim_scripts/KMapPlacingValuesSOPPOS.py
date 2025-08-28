from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService

class KMapPlacingValuesSOPPOS(VoiceoverScene):
    def construct(self):
        # Set the speech service for text-to-speech
        self.set_speech_service(GTTSService())

        # --- Scene Setup: Title ---
        # Create the main title for the scene
        title = Text("Placing Values", font_size=50, weight=BOLD).to_edge(UP)
        self.play(FadeIn(title))

        # --- SoP Explanation ---
        # Define narration and text content for the SoP heading
        sop_heading_narration = "Placing Values: For SoP expressions or Canonical Sums, also known as ON sets:"
        sop_heading_text_content = "For SoP expressions or Canonical Sums (ON sets):"
        sop_heading = Text(
            sop_heading_text_content,
            t2c={
                "SoP expressions": BLUE,
                "Canonical Sums": GREEN,
                "(ON sets)": YELLOW
            },
            font_size=36
        ).next_to(title, DOWN, buff=0.8).to_edge(LEFT, buff=0.5)

        # Synchronize displaying the SoP heading with narration
        with self.voiceover(text=sop_heading_narration) as tracker:
            self.play(Write(sop_heading), run_time=tracker.duration * 0.8)
            # A short wait to let the narration finish naturally if animation is faster
            self.wait(tracker.duration * 0.2)

        # Visualize a K-map cell and the value '1'
        kmap_cell = Square(side_length=1.5, color=GREY_A, fill_opacity=0.2)
        # Position the cell on the left side of the screen
        kmap_cell.move_to(LEFT * (self.camera.frame_width / 4))
        one_value = Text("1", font_size=72, color=RED).move_to(kmap_cell.get_center())

        # Define narration and text content for the SoP explanation
        sop_explanation_narration = "Place a '1' in the K-map cell corresponding to each minterm where the function's output is '1'."
        sop_explanation_text_content = "Place a '1' in the K-map cell corresponding to each minterm where the function's output is '1'."
        sop_explanation = Text(
            sop_explanation_text_content,
            t2c={
                "'1'": RED,
                "minterm": TEAL,
                "function's output is '1'": PURPLE
            },
            font_size=32
        )
        # Position the explanation text on the right side, aligned with the top of the cell
        sop_explanation.move_to(RIGHT * (self.camera.frame_width / 4)).align_to(kmap_cell, UP)

        # Synchronize placing the '1' and displaying the explanation with narration
        with self.voiceover(text=sop_explanation_narration) as tracker:
            self.play(
                FadeIn(kmap_cell),          # Show the K-map cell
                FadeIn(one_value, shift=UP), # Animate placing the '1' by fading in from top
                Write(sop_explanation),      # Write out the explanation text
                run_time=tracker.duration
            )
            self.wait(tracker.duration) # Wait for the narration to complete

        self.wait(1) # Pause before transitioning to the next section

        # --- PoS Explanation ---
        # Define narration and text content for the PoS heading
        pos_heading_narration = "For PoS expressions or Canonical Products, also known as OFF sets:"
        pos_heading_text_content = "For PoS expressions or Canonical Products (OFF sets):"
        pos_heading = Text(
            pos_heading_text_content,
            t2c={
                "PoS expressions": BLUE,
                "Canonical Products": GREEN,
                "(OFF sets)": YELLOW
            },
            font_size=36
        ).next_to(title, DOWN, buff=0.8).to_edge(LEFT, buff=0.5)

        # Define narration and text content for the PoS explanation
        pos_explanation_narration = "Place a '0' in the K-map cell corresponding to each maxterm where the function's output is '0'."
        pos_explanation_text_content = "Place a '0' in the K-map cell corresponding to each maxterm where the function's output is '0'."
        pos_explanation = Text(
            pos_explanation_text_content,
            t2c={
                "'0'": RED,
                "maxterm": TEAL,
                "function's output is '0'": PURPLE
            },
            font_size=32
        )
        # Position the explanation text on the right side, aligned with the top of the cell
        pos_explanation.move_to(RIGHT * (self.camera.frame_width / 4)).align_to(kmap_cell, UP)

        # Animate the transition from SoP content to PoS content
        with self.voiceover(text=pos_heading_narration) as tracker:
            self.play(
                Transform(sop_heading, pos_heading), # Transform the SoP heading into the PoS heading
                FadeOut(sop_explanation, shift=UP), # Fade out the old SoP explanation
                FadeOut(one_value),                  # Remove the '1' from the cell
                run_time=tracker.duration
            )
            self.wait(tracker.duration) # Wait for the narration to complete
        
        # Create the '0' value to be placed in the K-map cell
        zero_value = Text("0", font_size=72, color=RED).move_to(kmap_cell.get_center())

        # Synchronize placing the '0' and displaying the explanation with narration
        with self.voiceover(text=pos_explanation_narration) as tracker:
            self.play(
                FadeIn(zero_value, shift=UP), # Animate placing the '0' by fading in from top
                Write(pos_explanation),      # Write out the new PoS explanation text
                run_time=tracker.duration
            )
            self.wait(tracker.duration) # Wait for the narration to complete

        self.wait(1) # Pause before cleaning up the scene

        # --- Final Cleanup ---
        # Fade out all remaining mobjects from the scene
        self.play(
            FadeOut(title),
            # sop_heading now holds the transformed pos_heading, so fading it out removes the PoS heading
            FadeOut(sop_heading), 
            FadeOut(kmap_cell),
            FadeOut(zero_value),
            FadeOut(pos_explanation)
        )
        self.wait(1) # Final short pause