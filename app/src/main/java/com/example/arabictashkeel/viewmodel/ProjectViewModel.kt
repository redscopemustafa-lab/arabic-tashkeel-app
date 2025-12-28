package com.example.arabictashkeel.viewmodel

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.core.content.FileProvider
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.arabictashkeel.data.ProjectRepository
import java.io.File
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

data class ShareUiState(
    val inProgress: Boolean = false,
    val sharedUri: Uri? = null,
    val error: String? = null,
)

class ProjectViewModel(
    private val repository: ProjectRepository,
    private val dispatcher: CoroutineDispatcher = Dispatchers.IO,
) : ViewModel() {

    private val _shareState = MutableStateFlow(ShareUiState())
    val shareState: StateFlow<ShareUiState> = _shareState.asStateFlow()

    fun shareProject(context: Context) {
        viewModelScope.launch {
            _shareState.update { ShareUiState(inProgress = true) }
            try {
                val export = withContext(dispatcher) { repository.exportProject(context.cacheDir) }
                val uri = FileProvider.getUriForFile(
                    context,
                    "${context.packageName}.provider",
                    export,
                )
                startShareIntent(context, uri)
                _shareState.update { ShareUiState(inProgress = false, sharedUri = uri) }
            } catch (t: Throwable) {
                _shareState.update {
                    ShareUiState(
                        inProgress = false,
                        error = t.localizedMessage ?: "Unable to share project",
                    )
                }
            }
        }
    }

    suspend fun exportProject(context: Context): File = withContext(dispatcher) {
        repository.exportProject(context.cacheDir)
    }

    private fun startShareIntent(context: Context, uri: Uri) {
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "application/json"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        context.startActivity(Intent.createChooser(intent, "Share project"))
    }
}
