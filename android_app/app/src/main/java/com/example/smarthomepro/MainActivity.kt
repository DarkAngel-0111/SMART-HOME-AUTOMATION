package com.example.smarthomepro

import android.annotation.SuppressLint
import android.content.Context
import android.os.Bundle
import android.view.ViewGroup
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            SmartHomeApp()
        }
    }
}

@SuppressLint("SetJavaScriptEnabled")
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SmartHomeApp() {
    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences("smarthome_prefs", Context.MODE_PRIVATE) }

    var savedIp by remember { mutableStateOf(prefs.getString("gateway_ip", "") ?: "") }
    var savedPort by remember { mutableStateOf(prefs.getString("gateway_port", "5000") ?: "5000") }

    var ipInput by remember { mutableStateOf(if (savedIp.isNotEmpty()) savedIp else "192.168.1.") }
    var portInput by remember { mutableStateOf(savedPort) }

    var isConnected by remember { mutableStateOf(savedIp.isNotEmpty()) }
    var webViewRef by remember { mutableStateOf<WebView?>(null) }
    var pageError by remember { mutableStateOf(false) }

    val connectToGateway = {
        val cleanIp = ipInput.trim().removePrefix("http://").removePrefix("https://")
        val cleanPort = portInput.trim()
        if (cleanIp.isNotEmpty()) {
            savedIp = cleanIp
            savedPort = cleanPort
            prefs.edit().putString("gateway_ip", cleanIp).putString("gateway_port", cleanPort).apply()
            pageError = false
            isConnected = true
            webViewRef?.loadUrl("http://$cleanIp:$cleanPort")
        }
    }

    BackHandler(enabled = isConnected) {
        if (webViewRef?.canGoBack() == true) {
            webViewRef?.goBack()
        } else {
            isConnected = false
        }
    }

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = Color(0xFF07090E)
    ) {
        if (!isConnected) {
            // Setup & IP Entry Screen
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(24.dp),
                contentAlignment = Alignment.Center
            ) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(24.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF121826)),
                    elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = "⚡",
                            fontSize = 42.sp
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "SmartHome Pro",
                            fontSize = 24.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFFF8FAFC)
                        )
                        Text(
                            text = "Arduino Uno • MQTT • Automation",
                            fontSize = 12.sp,
                            color = Color(0xFF38BDF8),
                            fontWeight = FontWeight.SemiBold
                        )

                        Spacer(modifier = Modifier.height(24.dp))

                        Text(
                            text = "Enter Gateway IP Address:",
                            fontSize = 14.sp,
                            color = Color(0xFF94A3B8),
                            modifier = Modifier.align(Alignment.Start)
                        )
                        Spacer(modifier = Modifier.height(6.dp))

                        OutlinedTextField(
                            value = ipInput,
                            onValueChange = { ipInput = it },
                            placeholder = { Text("e.g. 192.168.1.100", color = Color(0xFF64748B)) },
                            singleLine = true,
                            keyboardOptions = KeyboardOptions(
                                keyboardType = KeyboardType.Number,
                                imeAction = ImeAction.Next
                            ),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedTextColor = Color.White,
                                unfocusedTextColor = Color.White,
                                focusedBorderColor = Color(0xFF38BDF8),
                                unfocusedBorderColor = Color(0xFF334155),
                                cursorColor = Color(0xFF38BDF8)
                            ),
                            modifier = Modifier.fillMaxWidth()
                        )

                        Spacer(modifier = Modifier.height(14.dp))

                        Text(
                            text = "Port (Default 5000):",
                            fontSize = 14.sp,
                            color = Color(0xFF94A3B8),
                            modifier = Modifier.align(Alignment.Start)
                        )
                        Spacer(modifier = Modifier.height(6.dp))

                        OutlinedTextField(
                            value = portInput,
                            onValueChange = { portInput = it },
                            placeholder = { Text("5000", color = Color(0xFF64748B)) },
                            singleLine = true,
                            keyboardOptions = KeyboardOptions(
                                keyboardType = KeyboardType.Number,
                                imeAction = ImeAction.Done
                            ),
                            keyboardActions = KeyboardActions(onDone = { connectToGateway() }),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedTextColor = Color.White,
                                unfocusedTextColor = Color.White,
                                focusedBorderColor = Color(0xFF38BDF8),
                                unfocusedBorderColor = Color(0xFF334155),
                                cursorColor = Color(0xFF38BDF8)
                            ),
                            modifier = Modifier.fillMaxWidth()
                        )

                        Spacer(modifier = Modifier.height(24.dp))

                        Button(
                            onClick = connectToGateway,
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(52.dp),
                            shape = RoundedCornerShape(14.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0284C7))
                        ) {
                            Text(
                                text = "CONNECT TO SMART HOME",
                                fontSize = 15.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color.White
                            )
                        }

                        Spacer(modifier = Modifier.height(18.dp))

                        // Quick Presets
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            TextButton(onClick = {
                                ipInput = "10.0.2.2"
                                portInput = "5000"
                            }) {
                                Text("Emulator (10.0.2.2)", fontSize = 11.sp, color = Color(0xFF64748B))
                            }
                            TextButton(onClick = {
                                ipInput = "127.0.0.1"
                                portInput = "5000"
                            }) {
                                Text("Localhost", fontSize = 11.sp, color = Color(0xFF64748B))
                            }
                        }
                    }
                }
            }
        } else {
            // Connected: Full Screen Web Dashboard + Top Mini Bar
            Column(modifier = Modifier.fillMaxSize()) {
                // Top Mini Bar
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .statusBarsPadding()
                        .background(Color(0xFF0E1420))
                        .padding(horizontal = 14.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(text = "● ", color = if (pageError) Color(0xFFEF4444) else Color(0xFF10B981), fontSize = 14.sp)
                        Text(
                            text = "$savedIp:$savedPort",
                            color = Color(0xFFCBD5E1),
                            fontSize = 13.sp,
                            fontWeight = FontWeight.SemiBold
                        )
                    }

                    Row {
                        IconButton(onClick = { webViewRef?.reload() }) {
                            Text("🔄", fontSize = 16.sp)
                        }
                        IconButton(onClick = { isConnected = false }) {
                            Text("⚙️", fontSize = 16.sp)
                        }
                    }
                }

                // Main WebView
                Box(modifier = Modifier.fillMaxSize()) {
                    AndroidView(
                        factory = { ctx ->
                            WebView(ctx).apply {
                                layoutParams = ViewGroup.LayoutParams(
                                    ViewGroup.LayoutParams.MATCH_PARENT,
                                    ViewGroup.LayoutParams.MATCH_PARENT
                                )
                                settings.javaScriptEnabled = true
                                settings.domStorageEnabled = true
                                settings.databaseEnabled = true
                                settings.allowFileAccess = true
                                settings.allowContentAccess = true
                                settings.useWideViewPort = true
                                settings.loadWithOverviewMode = true
                                settings.mediaPlaybackRequiresUserGesture = false
                                settings.cacheMode = WebSettings.LOAD_DEFAULT

                                webViewClient = object : WebViewClient() {
                                    override fun onReceivedError(
                                        view: WebView?,
                                        errorCode: Int,
                                        description: String?,
                                        failingUrl: String?
                                    ) {
                                        pageError = true
                                    }
                                }
                                webChromeClient = WebChromeClient()

                                loadUrl("http://$savedIp:$savedPort")
                                webViewRef = this
                            }
                        },
                        modifier = Modifier.fillMaxSize()
                    )

                    // Error Overlay if Connection Fails
                    if (pageError) {
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
                                .background(Color(0xEE07090E))
                                .padding(24.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Card(
                                shape = RoundedCornerShape(20.dp),
                                colors = CardDefaults.cardColors(containerColor = Color(0xFF1E293B))
                            ) {
                                Column(
                                    modifier = Modifier.padding(24.dp),
                                    horizontalAlignment = Alignment.CenterHorizontally
                                ) {
                                    Text(text = "⚠️", fontSize = 36.sp)
                                    Spacer(modifier = Modifier.height(8.dp))
                                    Text(
                                        text = "Connection Failed",
                                        fontWeight = FontWeight.Bold,
                                        color = Color(0xFFEF4444),
                                        fontSize = 18.sp
                                    )
                                    Spacer(modifier = Modifier.height(8.dp))
                                    Text(
                                        text = "Unable to connect to http://$savedIp:$savedPort.\n\nMake sure your Arduino Gateway is running (python3 app.py) and your phone is on the same Wi-Fi.",
                                        color = Color(0xFFCBD5E1),
                                        fontSize = 13.sp
                                    )
                                    Spacer(modifier = Modifier.height(20.dp))
                                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                                        Button(
                                            onClick = {
                                                pageError = false
                                                webViewRef?.loadUrl("http://$savedIp:$savedPort")
                                            },
                                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0284C7))
                                        ) {
                                            Text("Retry")
                                        }
                                        OutlinedButton(onClick = { isConnected = false }) {
                                            Text("Change IP", color = Color(0xFF38BDF8))
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
