bl_info = {
    "name": "Photo Slide Show Creator",
    "blender": (2, 80, 0),
    "category": "Sequencer",
    "author": "Ram Kulkarni",
    "description": "Provides tools to navigate, scale and create slide shows after images are added in Blender Sequencer"
}

import bpy
import time
import math

## Create slide duration property
durationPropName = "slide_duration"
slideShowDuration = bpy.props.IntProperty (
    name = "Slide Duration",
    default = 5
)


## Operators for turning the image by 90 degrees to the left or right
class RotateLeftOperator(bpy.types.Operator):
    bl_idname = "opr.seq_rotate_left"
    bl_label = "Rotate Left"
    
    def execute(self, context):
        sortedSeqs[context.scene.frame_current-1].transform.rotation += 3.14 / 2
        return {'FINISHED'}

class RotateRightOperator(bpy.types.Operator):
    bl_idname = "opr.seq_rotate_right"
    bl_label = "Rotate Right"
    
    def execute(self, context):
        sortedSeqs[context.scene.frame_current-1].transform.rotation -= 3.14 / 2
        return {'FINISHED'}


## Operators for moving to next or previous frames
class NextFrameOperator(bpy.types.Operator):
    bl_idname = "opr.seq_next_frame"
    bl_label = "Next Frame"
    
    def execute(self, context):
        context.scene.frame_current += 1
        return {"FINISHED"}
    
class PrevFrameOperator(bpy.types.Operator):
    bl_idname = "opr.seq_prev_frame"
    bl_label = "Prev Frame"
    
    def execute(self, context): 
        if (context.scene.frame_current > 0):
            context.scene.frame_current -= 1
        return {"FINISHED"}

## operator to fix scale of each image so that it fits the render size
class FixScaleOperator(bpy.types.Operator):
    bl_idname = "opr.seq_fix_image_scale"
    bl_label = "Fix Image Scale"
    
    def execute(self, context):
        seqs = context.scene.sequence_editor.sequences_all
        bpy.ops.sequencer.reload()
        render_res_x = context.scene.render.resolution_x
        render_res_y = context.scene.render.resolution_y
        for seq in seqs:
            if (seq.type == 'IMAGE'):
                seq.select = True
                self.process_image(seq, render_res_x, render_res_y)
        return {'FINISHED'}
                
    def process_image(self, img, render_res_x, render_res_y):
        img.select = True
        seqElement = img.elements[0]
        image_width = seqElement.orig_width
        image_height = seqElement.orig_height
        
        if (abs(round(math.degrees(img.transform.rotation), 0)) == 90):
            tmp = image_width
            image_width = image_height
            image_height = tmp
        
        scale_x = render_res_x / image_width
        scale_y = render_res_y / image_height
        
        scale = scale_x
        if scale_y < scale_x : 
            scale = scale_y
            
        img.transform.scale_x = scale
        img.transform.scale_y = scale
        

## Operator to create slide show of specified duration. It also sets output to mpeg4 and audio codec to mp3
class SetSlideShowDurationOpration(bpy.types.Operator):
    bl_idname = "opr.seq_set_slide_show_duration"
    bl_label = "Set Slide Show Duration"
    
    def execute(self, context):    
        bpy.ops.sequencer.select_all(action="SELECT")
        bpy.ops.sequencer.meta_make()
        bpy.context.scene.sequence_editor.sequences.new_effect(name="speed", type="SPEED", channel=2, frame_start=bpy.context.active_sequence_strip.frame_final_start, frame_end=bpy.context.active_sequence_strip.frame_final_end, seq1=bpy.context.active_sequence_strip)
        bpy.context.active_sequence_strip.frame_final_end = bpy.context.scene.render.fps * bpy.context.active_sequence_strip.frame_duration * bpy.context.scene.slide_duration
        bpy.context.scene.frame_end = bpy.context.active_sequence_strip.frame_final_end
        bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
        bpy.context.scene.render.ffmpeg.format = 'MPEG4'
        bpy.context.scene.render.ffmpeg.audio_codec = 'MP3'
        return {'FINISHED'}

## Initializer operator. Must be called every time new slide show is to be created
## It also separates images
class InitOperator(bpy.types.Operator):
    bl_idname = "opr.seq_image_slide_show_init"
    bl_label = "Initialize Image Slide Show Addon"
    
    def execute(self, context):
        # build array of frames 
        global count, sortedSeqs
        
        count = len(bpy.context.scene.sequence_editor.sequences_all[:])
        
        if (count == 1):
            # assuming this is an image sequence with multiple images. We will separate images
            bpy.context.scene.sequence_editor.sequences_all[0].select = True
            bpy.ops.sequencer.images_separate()
            count = len(bpy.context.scene.sequence_editor.sequences_all[:])
            
        print("Count = ", count)
        
        sortedSeqs = [None] * count
                
        for seq in bpy.context.scene.sequence_editor.sequences_all:
            sortedSeqs[seq.frame_final_start-1] =  seq
           
        return {'FINISHED'}


## UI panel for this add on
class PhotoSlideshowPanel(bpy.types.Panel):
    bl_idname = "SEQ_PT_Photo_Slideshow_Panel"
    bl_label = "Photo Slide Show"
    # see https://docs.blender.org/api/current/bpy.types.Panel.html?#bpy.types.Panel.bl_space_type
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    
    def draw(self, context):
        self.layout.label(text="Photo Slide Show Label ---")
        
        col = self.layout.column()
        row1 = col.row()
        #row1.prop(context.scene, durationPropName)
        row1.operator("opr.seq_image_slide_show_init", text="Initialize")
        
        row2 = col.row()
        col2_1 = row2.column()
        col2_1.operator("opr.seq_prev_frame", text="Prev")
        col2_2 = row2.column()
        col2_2.operator("opr.seq_next_frame", text="Next")
        
        row3 = col.row()
        col3_1 = row3.column()
        col3_1.operator("opr.seq_rotate_left", text="Rotate Left")
        col3_2 = row3.column()
        col3_2.operator("opr.seq_rotate_right", text="Rotate Right")
        
        row4 = col.row()
        row4.operator("opr.seq_fix_image_scale", text="Fix Scale")
        
        row5 = col.row()
        row5.prop(context.scene, durationPropName)
        
        row6 = col.row()
        row6.operator("opr.seq_set_slide_show_duration", text="Finish")
        

addonClasses = (
    PrevFrameOperator,
    NextFrameOperator,
    RotateLeftOperator,
    RotateRightOperator,
    FixScaleOperator,
    InitOperator,
    SetSlideShowDurationOpration,
    PhotoSlideshowPanel
)

def register():
    setattr(bpy.types.Scene, durationPropName, slideShowDuration)     
    for cls in addonClasses:
        bpy.utils.register_class(cls)

def unregister():
    for cls in addonClasses:
        bpy.utils.unregister_class(cls)
