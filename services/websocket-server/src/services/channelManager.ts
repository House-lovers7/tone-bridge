import { logger } from '../utils/logger';

interface UserPresence {
  userId: string;
  status: 'online' | 'away' | 'busy' | 'offline';
  lastSeen: Date;
  channels: Set<string>;
}

interface ChannelInfo {
  name: string;
  type: 'public' | 'private' | 'direct';
  members: Set<string>;
  createdAt: Date;
  metadata?: any;
}

export class ChannelManager {
  private channels: Map<string, ChannelInfo>;
  private userPresence: Map<string, UserPresence>;
  private channelPermissions: Map<string, Set<string>>; // channel -> allowed users

  constructor() {
    this.channels = new Map();
    this.userPresence = new Map();
    this.channelPermissions = new Map();
    
    // Initialize default channels
    this.initializeDefaultChannels();
  }

  private initializeDefaultChannels() {
    // Create default public channels
    const defaultChannels = [
      'transformations',
      'analysis',
      'auto-transform',
      'general',
      'notifications'
    ];

    defaultChannels.forEach(channelName => {
      this.createChannel(channelName, 'public');
    });

    logger.info(`Initialized ${defaultChannels.length} default channels`);
  }

  createChannel(
    name: string, 
    type: 'public' | 'private' | 'direct' = 'public',
    metadata?: any
  ): ChannelInfo {
    if (this.channels.has(name)) {
      return this.channels.get(name)!;
    }

    const channel: ChannelInfo = {
      name,
      type,
      members: new Set(),
      createdAt: new Date(),
      metadata
    };

    this.channels.set(name, channel);
    
    // Public channels are accessible to all
    if (type === 'public') {
      this.channelPermissions.set(name, new Set(['*']));
    } else {
      this.channelPermissions.set(name, new Set());
    }

    logger.info(`Created channel: ${name} (${type})`);
    return channel;
  }

  deleteChannel(name: string): boolean {
    if (!this.channels.has(name)) {
      return false;
    }

    // Remove channel
    this.channels.delete(name);
    this.channelPermissions.delete(name);

    // Remove channel from all user presence
    this.userPresence.forEach(presence => {
      presence.channels.delete(name);
    });

    logger.info(`Deleted channel: ${name}`);
    return true;
  }

  async validateAccess(userId: string, channelName: string): Promise<boolean> {
    // Check if channel exists
    const channel = this.channels.get(channelName);
    if (!channel) {
      // Auto-create channel if it doesn't exist (for dynamic channels)
      this.createChannel(channelName, 'public');
      return true;
    }

    // Public channels are accessible to all
    if (channel.type === 'public') {
      return true;
    }

    // Check permissions
    const permissions = this.channelPermissions.get(channelName);
    if (!permissions) {
      return false;
    }

    // Check if user has explicit permission or wildcard access
    return permissions.has(userId) || permissions.has('*');
  }

  grantAccess(userId: string, channelName: string): void {
    const permissions = this.channelPermissions.get(channelName);
    if (permissions) {
      permissions.add(userId);
      logger.info(`Granted access to ${userId} for channel ${channelName}`);
    }
  }

  revokeAccess(userId: string, channelName: string): void {
    const permissions = this.channelPermissions.get(channelName);
    if (permissions) {
      permissions.delete(userId);
      logger.info(`Revoked access from ${userId} for channel ${channelName}`);
    }
  }

  addUserToChannel(userId: string, channelName: string): void {
    const channel = this.channels.get(channelName);
    if (channel) {
      channel.members.add(userId);
    }

    // Update user presence
    const presence = this.userPresence.get(userId);
    if (presence) {
      presence.channels.add(channelName);
    }
  }

  removeUserFromChannel(userId: string, channelName: string): void {
    const channel = this.channels.get(channelName);
    if (channel) {
      channel.members.delete(userId);
    }

    // Update user presence
    const presence = this.userPresence.get(userId);
    if (presence) {
      presence.channels.delete(channelName);
    }
  }

  updatePresence(userId: string, status: string): void {
    let presence = this.userPresence.get(userId);
    
    if (!presence) {
      presence = {
        userId,
        status: status as any,
        lastSeen: new Date(),
        channels: new Set()
      };
      this.userPresence.set(userId, presence);
    } else {
      presence.status = status as any;
      presence.lastSeen = new Date();
    }

    logger.debug(`Updated presence for ${userId}: ${status}`);
  }

  getPresence(userId: string): UserPresence | undefined {
    return this.userPresence.get(userId);
  }

  getChannelMembers(channelName: string): string[] {
    const channel = this.channels.get(channelName);
    return channel ? Array.from(channel.members) : [];
  }

  getUserChannels(userId: string): string[] {
    const presence = this.userPresence.get(userId);
    return presence ? Array.from(presence.channels) : [];
  }

  getChannelInfo(channelName: string): ChannelInfo | undefined {
    return this.channels.get(channelName);
  }

  getAllChannels(): ChannelInfo[] {
    return Array.from(this.channels.values());
  }

  getPublicChannels(): ChannelInfo[] {
    return Array.from(this.channels.values()).filter(ch => ch.type === 'public');
  }

  getOnlineUsers(): string[] {
    return Array.from(this.userPresence.entries())
      .filter(([_, presence]) => presence.status === 'online')
      .map(([userId, _]) => userId);
  }

  cleanupInactiveUsers(inactiveThresholdMs: number = 30 * 60 * 1000): void {
    const now = new Date();
    const usersToRemove: string[] = [];

    this.userPresence.forEach((presence, userId) => {
      const timeSinceLastSeen = now.getTime() - presence.lastSeen.getTime();
      
      if (timeSinceLastSeen > inactiveThresholdMs && presence.status === 'offline') {
        usersToRemove.push(userId);
      }
    });

    usersToRemove.forEach(userId => {
      // Remove from all channels
      this.userPresence.get(userId)?.channels.forEach(channelName => {
        this.removeUserFromChannel(userId, channelName);
      });
      
      // Remove presence
      this.userPresence.delete(userId);
      
      logger.info(`Cleaned up inactive user: ${userId}`);
    });
  }

  getStatistics(): any {
    return {
      totalChannels: this.channels.size,
      publicChannels: this.getPublicChannels().length,
      privateChannels: this.channels.size - this.getPublicChannels().length,
      totalUsers: this.userPresence.size,
      onlineUsers: this.getOnlineUsers().length,
      channelDetails: Array.from(this.channels.entries()).map(([name, info]) => ({
        name,
        type: info.type,
        memberCount: info.members.size,
        createdAt: info.createdAt
      }))
    };
  }
}