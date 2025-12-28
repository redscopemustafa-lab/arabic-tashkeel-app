package com.example.arabictashkeel.data

import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class ProjectRepository(
    private val exportFileName: String = "project.json",
) {
    /**
     * Creates an export artifact for the current project and returns the written file.
     * Sharing concerns are intentionally kept outside the repository so the same export
     * routine can be reused by backups and share flows.
     */
    suspend fun exportProject(cacheDir: File): File = withContext(Dispatchers.IO) {
        val exportFile = File(cacheDir, exportFileName)
        exportFile.parentFile?.mkdirs()
        exportFile.writeText(buildExportPayload())
        exportFile
    }

    private fun buildExportPayload(): String {
        // TODO: replace with real serialization when project data model is available.
        return """{"project":"untitled","segments":[]}"""
    }
}
