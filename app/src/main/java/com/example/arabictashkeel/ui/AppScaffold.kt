package com.example.arabictashkeel.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Share
import androidx.compose.material.icons.filled.UploadFile
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SmallTopAppBar
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TextField
import androidx.compose.runtime.Composable
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.unit.dp
import com.example.arabictashkeel.model.Segment

enum class AppTab(val label: String) {
    Script("Script"),
    Player("Player"),
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppScaffold(
    modifier: Modifier = Modifier,
    onExportClick: () -> Unit,
    onShareClick: () -> Unit,
    onSegmentSaved: (Segment) -> Unit,
    scriptContent: @Composable (PaddingValues, (Segment) -> Unit) -> Unit,
    playerContent: @Composable (PaddingValues) -> Unit,
) {
    var selectedTab by rememberSaveable { mutableStateOf(AppTab.Script) }
    val segmentState = remember { mutableStateOf<Segment?>(null) }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        topBar = {
            SmallTopAppBar(
                title = { Text("Project") },
                actions = {
                    IconButton(onClick = onExportClick) {
                        Icon(Icons.Default.UploadFile, contentDescription = "Export")
                    }
                    IconButton(onClick = onShareClick) {
                        Icon(Icons.Default.Share, contentDescription = "Share")
                    }
                },
            )
        },
        floatingActionButton = {
            if (selectedTab == AppTab.Script) {
                FloatingActionButton(onClick = { segmentState.value = Segment() }) {
                    Icon(Icons.Default.Add, contentDescription = "Add segment")
                }
            }
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
        ) {
            TabRow(selectedTabIndex = selectedTab.ordinal) {
                AppTab.values().forEach { tab ->
                    Tab(
                        selected = selectedTab == tab,
                        onClick = { selectedTab = tab },
                        text = { Text(tab.label) },
                    )
                }
            }
            when (selectedTab) {
                AppTab.Script -> scriptContent(padding) { segment ->
                    segmentState.value = segment
                }
                AppTab.Player -> playerContent(padding)
            }
        }
        SegmentEditorDialog(segmentState, onDismiss = { segmentState.value = null }) { updated ->
            segmentState.value = null
            onSegmentSaved(updated)
        }
    }
}

@Composable
private fun SegmentEditorDialog(
    activeSegment: MutableState<Segment?>,
    onDismiss: () -> Unit,
    onSave: (Segment) -> Unit,
) {
    val segment = activeSegment.value ?: return
    var textValue by remember(segment.id) {
        mutableStateOf(TextFieldValue(segment.text))
    }
    var notesValue by remember(segment.id) {
        mutableStateOf(TextFieldValue(segment.notes.orEmpty()))
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Edit segment") },
        text = {
            Column {
                TextField(
                    value = textValue,
                    onValueChange = { textValue = it },
                    label = { Text("Content") },
                )
                TextField(
                    modifier = Modifier.padding(top = 8.dp),
                    value = notesValue,
                    onValueChange = { notesValue = it },
                    label = { Text("Notes (optional)") },
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    onSave(
                        segment.copy(
                            text = textValue.text,
                            notes = notesValue.text.ifEmpty { null },
                        ),
                    )
                },
            ) {
                Text("Save")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        },
    )
}
