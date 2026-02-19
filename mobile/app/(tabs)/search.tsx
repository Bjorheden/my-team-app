/**
 * Team search screen – search for teams and follow/unfollow.
 */

import { useState, useCallback } from "react";
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Team, PaginatedResponse } from "@/lib/types";

async function searchTeams(q: string): Promise<Team[]> {
  const res = await api.get<PaginatedResponse<Team>>("/teams/search", {
    params: { q, limit: 20 },
  });
  return res.data.items;
}

async function fetchFollows(): Promise<{ team_id: string }[]> {
  const res = await api.get<{ team_id: string }[]>("/me/follows");
  return res.data;
}

async function followTeam(team_id: string): Promise<void> {
  await api.post("/me/follows", { team_id });
}

async function unfollowTeam(team_id: string): Promise<void> {
  await api.delete(`/me/follows/${team_id}`);
}

function TeamRow({
  team,
  isFollowed,
  onToggle,
}: {
  team: Team;
  isFollowed: boolean;
  onToggle: () => void;
}) {
  return (
    <View style={styles.row}>
      <View style={styles.rowInfo}>
        <Text style={styles.teamName}>{team.name}</Text>
        {team.country && <Text style={styles.teamSub}>{team.country}</Text>}
      </View>
      <TouchableOpacity
        style={[styles.followBtn, isFollowed && styles.followBtnActive]}
        onPress={onToggle}
      >
        <Text style={styles.followBtnText}>{isFollowed ? "Following" : "Follow"}</Text>
      </TouchableOpacity>
    </View>
  );
}

export default function SearchScreen() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const queryClient = useQueryClient();

  // Simple debounce
  const onQueryChange = (text: string) => {
    setQuery(text);
    const t = setTimeout(() => setDebouncedQuery(text), 400);
    return () => clearTimeout(t);
  };

  const { data: teams, isLoading } = useQuery({
    queryKey: ["teams-search", debouncedQuery],
    queryFn: () => searchTeams(debouncedQuery),
    enabled: debouncedQuery.length >= 1,
  });

  const { data: follows } = useQuery({
    queryKey: ["follows"],
    queryFn: fetchFollows,
  });

  const followedIds = new Set((follows ?? []).map((f) => f.team_id));

  const followMutation = useMutation({
    mutationFn: followTeam,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["follows"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const unfollowMutation = useMutation({
    mutationFn: unfollowTeam,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["follows"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const toggleFollow = useCallback(
    (team: Team) => {
      if (followedIds.has(team.id)) {
        unfollowMutation.mutate(team.id);
      } else {
        followMutation.mutate(team.id);
      }
    },
    [followedIds, followMutation, unfollowMutation]
  );

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.input}
        placeholder="Search teams..."
        placeholderTextColor="#666"
        value={query}
        onChangeText={onQueryChange}
        autoCapitalize="none"
      />

      {isLoading && debouncedQuery.length > 0 && (
        <ActivityIndicator style={styles.loader} color="#4f6ef7" />
      )}

      {!isLoading && debouncedQuery.length === 0 && (
        <Text style={styles.hint}>Type a team name to search.</Text>
      )}

      <FlatList
        data={teams ?? []}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <TeamRow
            team={item}
            isFollowed={followedIds.has(item.id)}
            onToggle={() => toggleFollow(item)}
          />
        )}
        ListEmptyComponent={
          debouncedQuery.length > 0 && !isLoading ? (
            <Text style={styles.hint}>No teams found for "{debouncedQuery}"</Text>
          ) : null
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#12122a", padding: 16 },
  input: {
    backgroundColor: "#1e1e3a",
    borderRadius: 10,
    padding: 12,
    color: "#fff",
    fontSize: 16,
    marginBottom: 12,
  },
  loader: { marginTop: 16 },
  hint: { color: "#555", textAlign: "center", marginTop: 32 },
  row: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#1e1e3a",
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
  },
  rowInfo: { flex: 1 },
  teamName: { color: "#fff", fontSize: 15, fontWeight: "600" },
  teamSub: { color: "#888", fontSize: 12, marginTop: 2 },
  followBtn: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "#4f6ef7",
  },
  followBtnActive: { backgroundColor: "#4f6ef7" },
  followBtnText: { color: "#fff", fontSize: 13, fontWeight: "500" },
});
