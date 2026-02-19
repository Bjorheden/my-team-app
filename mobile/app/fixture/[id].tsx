/**
 * Fixture detail page – shows fixture info + event timeline.
 */

import { useLocalSearchParams, Stack } from "expo-router";
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import api from "@/lib/api";
import { Fixture, Event } from "@/lib/types";

async function fetchFixture(id: string): Promise<Fixture> {
  const res = await api.get<Fixture>(`/fixtures/${id}`);
  return res.data;
}

async function fetchEvents(id: string): Promise<Event[]> {
  const res = await api.get<Event[]>(`/fixtures/${id}/events`);
  return res.data;
}

function EventRow({ event }: { event: Event }) {
  const icon =
    event.type === "goal" ? "⚽" : event.type === "card" ? "🟨" : event.type === "substitution" ? "🔄" : "•";
  return (
    <View style={styles.eventRow}>
      <Text style={styles.eventMinute}>{event.minute != null ? `${event.minute}'` : "–"}</Text>
      <Text style={styles.eventIcon}>{icon}</Text>
      <Text style={styles.eventPlayer}>{event.player_name ?? event.type}</Text>
    </View>
  );
}

export default function FixtureScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();

  const { data: fixture, isLoading: fixtureLoading } = useQuery({
    queryKey: ["fixture", id],
    queryFn: () => fetchFixture(id),
  });

  const { data: events, isLoading: eventsLoading } = useQuery({
    queryKey: ["fixture-events", id],
    queryFn: () => fetchEvents(id),
    refetchInterval: fixture?.status === "1H" || fixture?.status === "2H" ? 30_000 : false,
  });

  const isLoading = fixtureLoading || eventsLoading;

  const home = fixture?.home_team?.name ?? fixture?.home_team_id ?? "Home";
  const away = fixture?.away_team?.name ?? fixture?.away_team_id ?? "Away";
  const date = fixture ? format(new Date(fixture.start_time), "EEE d MMM yyyy · HH:mm") : "";
  const score =
    fixture?.home_score != null
      ? `${fixture.home_score}  –  ${fixture.away_score}`
      : "vs";

  return (
    <View style={styles.container}>
      <Stack.Screen options={{ title: "Match", headerShown: true }} />

      {isLoading ? (
        <ActivityIndicator style={styles.loader} color="#4f6ef7" />
      ) : (
        <>
          <View style={styles.header}>
            <Text style={styles.teams}>
              {home} {score} {away}
            </Text>
            <Text style={styles.date}>{date}</Text>
            <Text style={styles.statusBadge}>{fixture?.status}</Text>
          </View>

          {events && events.length > 0 && (
            <FlatList
              data={events}
              keyExtractor={(item) => item.id}
              renderItem={({ item }) => <EventRow event={item} />}
              contentContainerStyle={styles.eventsList}
              ListHeaderComponent={
                <Text style={styles.sectionTitle}>Match Events</Text>
              }
            />
          )}

          {events && events.length === 0 && (
            <Text style={styles.noEvents}>No events recorded yet.</Text>
          )}
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#12122a" },
  loader: { marginTop: 40 },
  header: { padding: 24, alignItems: "center", backgroundColor: "#1a1a35" },
  teams: { color: "#fff", fontSize: 18, fontWeight: "700", textAlign: "center" },
  date: { color: "#888", fontSize: 13, marginTop: 6 },
  statusBadge: {
    marginTop: 8,
    backgroundColor: "#4f6ef7",
    color: "#fff",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
    fontSize: 12,
    overflow: "hidden",
  },
  eventsList: { padding: 16 },
  sectionTitle: { color: "#888", fontSize: 12, textTransform: "uppercase", marginBottom: 10 },
  eventRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#1e1e3a",
    gap: 12,
  },
  eventMinute: { color: "#888", width: 36, textAlign: "right", fontSize: 13 },
  eventIcon: { fontSize: 18 },
  eventPlayer: { color: "#fff", flex: 1, fontSize: 14 },
  noEvents: { color: "#555", textAlign: "center", marginTop: 40 },
});
