/**
 * Dashboard – list of followed teams with next/last match and standing.
 */

import { useCallback } from "react";
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import api from "@/lib/api";
import { DashboardEntry } from "@/lib/types";
import { useAuthStore } from "@/store/authStore";

async function fetchDashboard(): Promise<DashboardEntry[]> {
  const res = await api.get<DashboardEntry[]>("/me/dashboard");
  return res.data;
}

function FixtureLine({
  label,
  fixture,
}: {
  label: string;
  fixture: DashboardEntry["next_fixture"] | DashboardEntry["last_fixture"];
}) {
  if (!fixture) return null;
  const date = format(new Date(fixture.start_time), "d MMM HH:mm");
  const home = fixture.home_team?.short_name ?? fixture.home_team_id.slice(0, 3).toUpperCase();
  const away = fixture.away_team?.short_name ?? fixture.away_team_id.slice(0, 3).toUpperCase();
  const score =
    fixture.home_score != null
      ? `${fixture.home_score}–${fixture.away_score}`
      : date;
  return (
    <Text style={styles.fixtureLine}>
      {label}: {home} {score} {away}
    </Text>
  );
}

function TeamCard({ entry }: { entry: DashboardEntry }) {
  const router = useRouter();
  return (
    <TouchableOpacity
      style={styles.card}
      onPress={() => router.push(`/team/${entry.team.id}`)}
    >
      <View style={styles.cardHeader}>
        <Text style={styles.teamName}>{entry.team.name}</Text>
        {entry.standing && (
          <Text style={styles.standing}>
            #{entry.standing.rank} · {entry.standing.points} pts
          </Text>
        )}
      </View>
      <FixtureLine label="Last" fixture={entry.last_fixture} />
      <FixtureLine label="Next" fixture={entry.next_fixture} />
    </TouchableOpacity>
  );
}

export default function DashboardScreen() {
  const { logout } = useAuthStore();
  const { data, isLoading, refetch, isError } = useQuery({
    queryKey: ["dashboard"],
    queryFn: fetchDashboard,
  });

  const renderItem = useCallback(
    ({ item }: { item: DashboardEntry }) => <TeamCard entry={item} />,
    []
  );

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#4f6ef7" />
      </View>
    );
  }

  if (isError) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Failed to load dashboard.</Text>
        <TouchableOpacity onPress={() => refetch()}>
          <Text style={styles.retry}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {!data || data.length === 0 ? (
        <View style={styles.center}>
          <Text style={styles.emptyText}>
            {"You're not following any teams yet.\nUse Search to find your teams!"}
          </Text>
        </View>
      ) : (
        <FlatList
          data={data}
          keyExtractor={(item) => item.team.id}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
          onRefresh={refetch}
          refreshing={isLoading}
        />
      )}
      <TouchableOpacity style={styles.logoutBtn} onPress={logout}>
        <Text style={styles.logoutText}>Log out</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#12122a" },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#12122a" },
  list: { padding: 16, gap: 12 },
  card: {
    backgroundColor: "#1e1e3a",
    borderRadius: 12,
    padding: 16,
    gap: 6,
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 4,
  },
  teamName: { color: "#fff", fontSize: 17, fontWeight: "600" },
  standing: { color: "#888", fontSize: 13 },
  fixtureLine: { color: "#ccc", fontSize: 13 },
  errorText: { color: "#f66", marginBottom: 12 },
  retry: { color: "#4f6ef7" },
  emptyText: { color: "#888", textAlign: "center", lineHeight: 24 },
  logoutBtn: { padding: 16, alignItems: "center" },
  logoutText: { color: "#777", fontSize: 13 },
});
