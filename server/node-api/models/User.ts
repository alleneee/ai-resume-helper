import mongoose, { Document, Schema } from 'mongoose';
import bcrypt from 'bcrypt';
import { nanoid } from 'nanoid';

// 用户角色枚举
export enum UserRole {
    USER = 'USER',
    PREMIUM = 'PREMIUM',
    ADMIN = 'ADMIN'
}

// 用户状态枚举
export enum UserStatus {
    ACTIVE = 'active',
    INACTIVE = 'inactive',
    SUSPENDED = 'suspended'
}

// 用户文档接口
export interface IUser extends Document {
    email: string;
    phoneNumber?: string;
    passwordHash: string;
    fullName: string;
    subscriptionTier: 'free' | 'pro' | 'enterprise';
    preferences: {
        preferredJobTitles?: string[];
        preferredLocations?: string[];
        preferredIndustries?: string[];
        salaryExpectations?: {
            min?: number;
            max?: number;
            currency?: string;
        };
        notificationSettings?: {
            email: boolean;
            browser: boolean;
            application: boolean;
        };
    };
    createdAt: Date;
    updatedAt: Date;
    lastLogin?: Date;
    comparePassword(candidatePassword: string): Promise<boolean>;
}

// 用户Schema定义
const UserSchema = new Schema<IUser>({
    email: {
        type: String,
        required: true,
        unique: true,
        trim: true,
        lowercase: true,
    },
    phoneNumber: {
        type: String,
        trim: true,
    },
    passwordHash: {
        type: String,
        required: true,
    },
    fullName: {
        type: String,
        required: true,
        trim: true,
    },
    subscriptionTier: {
        type: String,
        enum: ['free', 'pro', 'enterprise'],
        default: 'free',
    },
    preferences: {
        preferredJobTitles: [String],
        preferredLocations: [String],
        preferredIndustries: [String],
        salaryExpectations: {
            min: Number,
            max: Number,
            currency: {
                type: String,
                default: 'CNY',
            },
        },
        notificationSettings: {
            email: {
                type: Boolean,
                default: true,
            },
            browser: {
                type: Boolean,
                default: true,
            },
            application: {
                type: Boolean,
                default: true,
            },
        },
    },
    lastLogin: Date,
}, {
    timestamps: true,
    toJSON: {
        transform: function (_doc, ret) {
            delete ret.passwordHash;
            delete ret.__v;
            return ret;
        }
    }
});

// 创建索引
UserSchema.index({ email: 1 });
UserSchema.index({ subscriptionTier: 1 });

// 密码比较方法
UserSchema.methods.comparePassword = async function (
    candidatePassword: string
): Promise<boolean> {
    return bcrypt.compare(candidatePassword, this.passwordHash);
};

// 保存前的钩子：密码哈希
UserSchema.pre('save', async function (next) {
    const user = this;

    // 只有在密码被修改或是新用户时才哈希处理
    if (!user.isModified('passwordHash')) {
        return next();
    }

    try {
        const salt = await bcrypt.genSalt(10);
        user.passwordHash = await bcrypt.hash(user.passwordHash, salt);
        next();
    } catch (error: any) {
        next(error);
    }
});

// 生成验证令牌
UserSchema.methods.generateVerificationToken = function (): string {
    const user = this as IUser;
    const token = nanoid(32);
    user.verificationToken = token;
    return token;
};

// 生成密码重置令牌
UserSchema.methods.generatePasswordResetToken = async function (): Promise<string> {
    const user = this as IUser;
    const token = nanoid(32);
    user.passwordResetToken = token;
    user.passwordResetExpires = new Date(Date.now() + 3600000); // 1小时后过期
    await user.save();
    return token;
};

// 导出模型
const User = mongoose.model<IUser>('User', UserSchema);

export default User; 