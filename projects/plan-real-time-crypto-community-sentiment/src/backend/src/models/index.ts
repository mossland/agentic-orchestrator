import { Entity, PrimaryGeneratedColumn, Column, ManyToOne, OneToMany } from 'typeorm';

@Entity()
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ unique: true })
  username: string;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP' })
  created_at: Date;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP', onUpdate: 'CURRENT_TIMESTAMP' })
  updated_at: Date;
}

@Entity()
export class SentimentAnalysis {
  @PrimaryGeneratedColumn()
  id: number;

  @ManyToOne(() => User, (user) => user.sentiments)
  user: User;

  @Column({ type: 'text' })
  tweetContent: string;

  @Column({ type: 'float' })
  sentimentScore: number;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP' })
  created_at: Date;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP', onUpdate: 'CURRENT_TIMESTAMP' })
  updated_at: Date;
}

@Entity()
export class BlockchainTransaction {
  @PrimaryGeneratedColumn()
  id: number;

  @ManyToOne(() => User, (user) => user.transactions)
  user: User;

  @Column({ type: 'text' })
  transactionHash: string;

  @Column({ type: 'text' })
  network: string;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP' })
  created_at: Date;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP', onUpdate: 'CURRENT_TIMESTAMP' })
  updated_at: Date;
}

@Entity()
export class ExternalAPIIntegration {
  @PrimaryGeneratedColumn()
  id: number;

  @ManyToOne(() => User, (user) => user.apiIntegrations)
  user: User;

  @Column({ type: 'text' })
  apiName: string;

  @Column({ type: 'jsonb', nullable: true })
  apiKey?: Record<string, unknown>;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP' })
  created_at: Date;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP', onUpdate: 'CURRENT_TIMESTAMP' })
  updated_at: Date;
}

@Entity()
export class Service {
  @PrimaryGeneratedColumn()
  id: number;

  @ManyToOne(() => User, (user) => user.services)
  user: User;

  @Column({ type: 'text' })
  serviceName: string;

  @Column({ type: 'boolean', default: false })
  isActive: boolean;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP' })
  created_at: Date;

  @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP', onUpdate: 'CURRENT_TIMESTAMP' })
  updated_at: Date;
}