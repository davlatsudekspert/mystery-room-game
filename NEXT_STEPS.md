# Next Steps

1. Integrate the remaining Blender models as they land. Recalibrate the pivot and axis constants from `docs/models/*.md`, then rerun `qa/playthrough.tscn` until all steps happen through real 3D taps.
2. Lighting pass with the real room shell. Review the 1979 echo finale and the darkroom shadow puzzle visually.
3. Triangle and texture budget pass. Rebuild the APK and give the owner a debug APK for real-device testing (FPS, touch, load time).
4. Release AAB via Gradle (needs the upload key). The CI workflows run only with the owner's consent.
5. Chapter 2 design doc ("The Missing Scientist") and its data hooks (`choices.ch1_lens`, `ch1_shards`).
