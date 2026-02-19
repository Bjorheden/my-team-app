/**
 * Team detail page – shows upcoming and past fixtures.
 */

import { useLocalSearchParams, useRouter, Stack } from "expo-router";
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import api from "@/lib/api";
import { Fixture, PaginatedResponse } from "@/lib/types";

async function fetchTeamFixtures(teamId: string): Promise<Fixture[]> {
  const res = await api.get<PaginatedResponse<Fixture>>(`/teams/${teamId}/fixtures`);
  return res.data.items;
}

function FixtureCard({ fixture, onPress }: { fixture: Fixture; onPress: () => void }) {
  const date = format(new Date(fixture.start_time), "EEE d MMM · HH:mm");
  const home = fixture.home_team?.name ?? fixture.home_team_id;
  const away = fixture.away_team?.name ?? fixture.away_team_id;
  const scoreOrDate =
    fixture.home_score != null
      ? `${fixture.home_score} – ${fixture.away_score}`
      : date;

  return (
    <TouchableOpacity style={styles.card} onPress={onPress}>
      <Text style={styles.matchup}>
        {home} vs {away}
      </Text>
      <Text style={styles.score}>{scoreOrDate}</Text>
      <Text style={styles.status}>{fixture.status}</Text>
    </TouchableOpacity>
  );
}

export default function TeamScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();

  const { data: fixtures, isLoading } = useQuery({
    queryKey: ["team-fixtures", id],
    queryFn: () => fetchTeamFixtures(id),
  });

  return (
    <View style={styles.container}>
      <Stack.Screen options={{ title: "Team Fixtures", headerShown: true }} />

      {isLoading ? (
        <ActivityIndicator style={styles.loader} color="#4f6ef7" />
      ) : (
        <FlatList
          data={fixtures ?? []}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <FixtureCard
              fixture={item}
              onPress={() => router.push(`/fixture/${item.id}`)}
            />
          )}
          contentContainerStyle={styles.list}
          ListEmptyComponent={
            <Text style={styles.empty}>No fixtures found in this window.</Text>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#12122a" },
  loader: { marginTop: 40 },
  list: { padding: 16, gap: 10 },
  card: { backgroundColor: "#1e1e3a", borderRadius: 12, padding: 14 },
  matchup: { color: "#fff", fontSize: 15, fontWeight: "600", marginBottom: 6 },
  score: { color: "#4f6ef7", fontSize: 20, fontWeight: "700", marginBottom: 4 },
  status: { color: "#888", fontSize: 12 },
  empty: { color: "#555", textAlign: "center", marginTop: 40 },
});
