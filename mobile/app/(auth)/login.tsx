/**
 * Login / Onboarding screen.
 *
 * In development (APP_ENV=development) shows a "Dev Login" button for fast iteration.
 * In production shows the magic-link email form.
 */

import { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useAuthStore } from "@/store/authStore";

const IS_DEV = process.env.APP_ENV !== "production";

export default function LoginScreen() {
  const { requestLink, devLogin } = useAuthStore();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [verifyToken, setVerifyToken] = useState("");
  const { verifyToken: doVerify } = useAuthStore();

  const handleRequestLink = async () => {
    if (!email.trim()) return;
    setLoading(true);
    try {
      await requestLink(email.trim());
      setSent(true);
    } catch {
      Alert.alert("Error", "Failed to send magic link. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    if (!verifyToken.trim()) return;
    setLoading(true);
    try {
      await doVerify(verifyToken.trim());
    } catch {
      Alert.alert("Error", "Invalid or expired token.");
    } finally {
      setLoading(false);
    }
  };

  const handleDevLogin = async () => {
    setLoading(true);
    try {
      await devLogin("dev-user-001");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      Alert.alert("Dev login failed", msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={styles.inner}>
        <Text style={styles.logo}>⚽ MyTeams</Text>
        <Text style={styles.tagline}>Your personalized football hub</Text>

        {!sent ? (
          <>
            <TextInput
              style={styles.input}
              placeholder="your@email.com"
              placeholderTextColor="#666"
              keyboardType="email-address"
              autoCapitalize="none"
              value={email}
              onChangeText={setEmail}
            />
            <TouchableOpacity
              style={styles.button}
              onPress={handleRequestLink}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>Send magic link</Text>
              )}
            </TouchableOpacity>
          </>
        ) : (
          <>
            <Text style={styles.hint}>
              Check your inbox for a verification code and paste it below.
            </Text>
            <TextInput
              style={styles.input}
              placeholder="Paste code here"
              placeholderTextColor="#666"
              autoCapitalize="none"
              value={verifyToken}
              onChangeText={setVerifyToken}
            />
            <TouchableOpacity
              style={styles.button}
              onPress={handleVerify}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>Verify</Text>
              )}
            </TouchableOpacity>
          </>
        )}

        {IS_DEV && (
          <TouchableOpacity style={styles.devButton} onPress={handleDevLogin} disabled={loading}>
            <Text style={styles.devButtonText}>🛠 Dev Login (skip auth)</Text>
          </TouchableOpacity>
        )}
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#1a1a2e" },
  inner: { flex: 1, justifyContent: "center", padding: 24 },
  logo: { fontSize: 40, textAlign: "center", color: "#fff", marginBottom: 8 },
  tagline: { fontSize: 16, textAlign: "center", color: "#8888aa", marginBottom: 48 },
  input: {
    backgroundColor: "#2a2a4e",
    borderRadius: 10,
    padding: 14,
    color: "#fff",
    fontSize: 16,
    marginBottom: 16,
  },
  hint: { color: "#aaa", textAlign: "center", marginBottom: 16 },
  button: {
    backgroundColor: "#4f6ef7",
    borderRadius: 10,
    padding: 14,
    alignItems: "center",
    marginBottom: 16,
  },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "600" },
  devButton: {
    marginTop: 32,
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#555",
    alignItems: "center",
  },
  devButtonText: { color: "#aaa", fontSize: 14 },
});
